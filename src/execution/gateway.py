"""
执行网关模块
处理订单提交、状态轮询、异常恢复
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from ..models.schemas import Order, TradeSignal
from ..models.enums import OrderStatus, OrderSide, OrderType, SignalType
from ..models.repository import DataRepository
from ..collectors.okx_interface import OKXTradingInterface

logger = logging.getLogger("aosft")


class OrderStateMachine:
    VALID_TRANSITIONS = {
        OrderStatus.PENDING: [OrderStatus.PARTIAL_FILLED, OrderStatus.FILLED, OrderStatus.REJECTED, OrderStatus.CANCELLED],
        OrderStatus.PARTIAL_FILLED: [OrderStatus.FILLED, OrderStatus.CANCELLED],
        OrderStatus.FILLED: [],
        OrderStatus.REJECTED: [],
        OrderStatus.CANCELLED: [],
    }
    
    def can_transition(self, current: OrderStatus, target: OrderStatus) -> bool:
        return target in self.VALID_TRANSITIONS.get(current, [])
    
    def transition(self, current: OrderStatus, target: OrderStatus) -> OrderStatus:
        if not self.can_transition(current, target):
            raise ValueError(f"非法状态转换: {current.value} → {target.value}")
        return target


class OrderTimeoutManager:
    def __init__(self, repo: DataRepository, limit_timeout: int = 300, max_timeout: int = 1800):
        self.repo = repo
        self.limit_timeout = limit_timeout
        self.max_timeout = max_timeout
    
    def check_timeout(self, order: dict) -> Optional[str]:
        created_at = datetime.fromisoformat(order['created_at'])
        elapsed = (datetime.now() - created_at).total_seconds()
        
        if order['order_type'] == 'limit' and elapsed > self.limit_timeout:
            return 'limit_timeout'
        
        if elapsed > self.max_timeout:
            return 'max_timeout'
        
        return None
    
    def scan_and_handle_timeouts(self) -> list:
        active_orders = self.repo.load_active_orders()
        timeout_orders = []
        
        for order in active_orders:
            timeout_type = self.check_timeout(order)
            if timeout_type:
                timeout_orders.append({
                    'order': order,
                    'timeout_type': timeout_type
                })
        
        return timeout_orders


class OrderRecoveryHandler:
    def __init__(self, repo: DataRepository, trading_interface: OKXTradingInterface):
        self.repo = repo
        self.trading = trading_interface
    
    def handle_timeout(self, order: dict, timeout_type: str) -> Optional[dict]:
        logger.warning(
            f"[ORDER-RECOVERY] 订单超时处理: order_id={order['order_id']} "
            f"type={timeout_type}"
        )
        
        try:
            cancel_result = self.trading.cancel_order(
                order['order_id'], order['symbol']
            )
            self.repo.update_order_status(
                order['order_id'], OrderStatus.CANCELLED
            )
            logger.info(f"订单{order['order_id']}已撤销")
            
            if timeout_type == 'limit_timeout':
                market_order = self.trading.create_market_order(
                    order['symbol'], order['side'],
                    order['amount'] - order.get('filled_amount', 0)
                )
                logger.info(f"已改用市价单重新下单: {market_order.get('id')}")
                return market_order
            
        except Exception as e:
            logger.error(f"订单异常恢复失败: {e}")
        
        return None
    
    def handle_rejection(self, order: dict, error_message: str):
        logger.error(
            f"[ORDER-RECOVERY] 订单被拒绝: order_id={order['order_id']} "
            f"error={error_message}"
        )
        self.repo.update_order_status(
            order['order_id'], OrderStatus.REJECTED,
            error_message=error_message
        )


class ExecutionGateway:
    def __init__(
        self,
        repo: DataRepository,
        trading_interface: OKXTradingInterface,
        limit_order_timeout: int = 300,
        max_order_timeout: int = 1800
    ):
        self.repo = repo
        self.trading = trading_interface
        self.state_machine = OrderStateMachine()
        self.timeout_manager = OrderTimeoutManager(
            repo, limit_order_timeout, max_order_timeout
        )
        self.recovery_handler = OrderRecoveryHandler(repo, trading_interface)
    
    def execute_open(self, signal: TradeSignal, amount: float) -> Optional[dict]:
        logger.info(
            f"[EXECUTION] 执行开仓: {signal.symbol} amount={amount:.8f} "
            f"price={signal.price:.2f}"
        )
        
        try:
            ticker = self.trading.fetch_ticker(signal.symbol)
            bid_price = ticker.get('bid', signal.price)
            
            limit_order = self.trading.create_limit_order(
                symbol=signal.symbol,
                side='buy',
                amount=amount,
                price=bid_price
            )
            
            order = Order(
                order_id=limit_order['id'],
                symbol=signal.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                amount=amount,
                price=bid_price,
                status=OrderStatus.PENDING,
                timeout_at=(datetime.now() + timedelta(
                    seconds=self.timeout_manager.limit_timeout
                )).isoformat()
            )
            self.repo.save_order(order)
            
            filled = self._wait_for_fill(limit_order['id'], signal.symbol)
            
            if filled:
                logger.info(f"限价单成交: order_id={limit_order['id']}")
                return filled
            
            market_result = self._fallback_to_market(
                signal.symbol, amount, limit_order['id']
            )
            return market_result
            
        except Exception as e:
            logger.error(f"开仓执行失败: {e}", exc_info=True)
            return None
    
    def execute_close(self, signal: TradeSignal, amount: float) -> Optional[dict]:
        logger.info(
            f"[EXECUTION] 执行平仓: {signal.symbol} amount={amount:.8f}"
        )
        
        try:
            market_order = self.trading.create_market_order(
                symbol=signal.symbol,
                side='sell',
                amount=amount
            )
            
            order = Order(
                order_id=market_order['id'],
                symbol=signal.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                amount=amount,
                status=OrderStatus.FILLED,
                filled_amount=amount,
                avg_price=market_order.get('price', signal.price)
            )
            self.repo.save_order(order)
            
            logger.info(f"平仓成交: order_id={market_order['id']}")
            return market_order
            
        except Exception as e:
            logger.error(f"平仓执行失败: {e}", exc_info=True)
            return None
    
    def _wait_for_fill(self, order_id: str, symbol: str,
                       timeout: int = 300) -> Optional[dict]:
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                order = self.trading.fetch_order(order_id, symbol)
                status = order.get('status')
                
                if status == 'closed':
                    self.repo.update_order_status(
                        order_id, OrderStatus.FILLED,
                        filled_amount=order.get('filled', 0),
                        avg_price=order.get('price')
                    )
                    return order
                elif status == 'canceled':
                    self.repo.update_order_status(order_id, OrderStatus.CANCELLED)
                    return None
                elif status == 'rejected':
                    self.repo.update_order_status(
                        order_id, OrderStatus.REJECTED,
                        error_message="交易所拒绝"
                    )
                    return None
                
            except Exception as e:
                logger.warning(f"轮询订单状态失败: {e}")
            
            time.sleep(5)
        
        return None
    
    def _fallback_to_market(self, symbol: str, amount: float,
                            limit_order_id: str) -> Optional[dict]:
        logger.info(f"限价单超时，撤销并改用市价单: {limit_order_id}")
        
        try:
            self.trading.cancel_order(limit_order_id, symbol)
            self.repo.update_order_status(limit_order_id, OrderStatus.CANCELLED)
            
            market_order = self.trading.create_market_order(symbol, 'buy', amount)
            return market_order
            
        except Exception as e:
            logger.error(f"改用市价单失败: {e}")
            return None
    
    def check_and_recover_orders(self):
        timeout_orders = self.timeout_manager.scan_and_handle_timeouts()
        for item in timeout_orders:
            self.recovery_handler.handle_timeout(
                item['order'], item['timeout_type']
            )
