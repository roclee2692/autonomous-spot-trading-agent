# Binance Spot 接口边界

核验日期：2026-08-23。部署前应再次核验官方文档与实时响应。

- 公共市场数据建议基址：`https://data-api.binance.vision`
- Spot Testnet REST 基址：`https://testnet.binance.vision/api`
- 启动时读取 `/api/v3/exchangeInfo?symbol=BTCUSDT`
- 必须解析 `PRICE_FILTER`、`LOT_SIZE`、`MIN_NOTIONAL` 或 `NOTIONAL`，同时尊重交易状态与支持的订单类型
- 账户费率不是公共常量。签名调用 `GET /api/v3/account/commission?symbol=BTCUSDT`；具体订单可用 `POST /api/v3/order/test` 加 `computeCommissionRates=true` 验证
- 主网启动时调用 `GET /sapi/v1/account/apiRestrictions`；IP 限制和 Reading/Spot 必须开启，提款、内部转账、Universal Transfer、Margin、Futures、Options 与 Portfolio Margin 必须关闭
- Maker 优先使用 `LIMIT_MAKER`，不要用会立即成交的普通限价单假装 post-only
- 成交后用回报中的实际数量与手续费资产更新余额。下一张卖单数量必须基于实际可用 BTC，而非理论买入数量

官方来源：

- https://developers.binance.com/en/docs/products/spot/filters
- https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/account
- https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/trade
- https://developers.binance.com/en/docs/products/spot/testnet/rest-api
- https://developers.binance.com/en/docs/catalog/core-trading-wallet/api/rest-api/account#get-api-key-permission
- https://developers.binance.com/en/docs/catalog/vip-and-institutional-sub-account/api/rest-api/asset-management#universal-transfer

2026-08-23 的只读 BTCUSDT 快照仍显示 `tickSize=0.01 USDT`、`minQty/stepSize=0.00001 BTC`、`NOTIONAL.minNotional=5 USDT`。这只是验收证据，程序不得依赖此快照。
