# Crypto Market Structure

V1 只使用少量可解释输入：价格、短/中均线、成交量比、实现波动率、前区间高低点。ETF flow、funding、open interest 与 liquidation 只能作为结构化 Context，不能单独下单。

新闻系统与交易系统分离。普通新闻只提供 Context；高置信重大风险事件可 `VETO` 或 `PAUSE`，但不能直接产生大额订单。数据矛盾、过期或缺失时输出 `UNCERTAIN`。

