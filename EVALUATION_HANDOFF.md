# V1.0 Evaluation Handoff

验收日期：2026-08-23（Asia/Shanghai）

## 完成状态

### 已完成并离线验证

- 公共市场数据与实时 symbol filters
- Testnet/Mainnet HMAC 签名客户端和严格域名隔离
- Windows Credential Manager 凭证存取，Secret 不进入配置/日志/数据库
- Account、commission、API restrictions 主网权限预检
- API withdrawal/internal transfer/margin/futures/options/portfolio-margin 失败关闭
- `POST /api/v3/order/test`
- LIMIT_MAKER 下单、查询、撤单、open orders、myTrades
- clientOrderId 幂等；写超时转 `UNKNOWN`，不自动重试
- `resolve-unknown` 再查询；仅在人类精确确认交易所不存在该单后解除歧义锁
- SQLite orders/fills/theses/cycles/balance，Thesis 和 Fill 禁止修改/删除
- 启动对账；远端无本地 Thesis 的 Agent order 阻止运行
- 部分/完整 fills 和实际 fee asset 记录
- 买单成交后扣 BTC fee 与一个 step buffer，再建立配对卖单
- 六状态 Regime、成本/波动率 Grid、Core/Reserve、Kill Switch、News veto
- Stage 1 一单上限、Stage 2 六单/$100 上限
- 七天、本机、Stage、资金上限绑定的 Mainnet activation
- run-once、daemon、状态、Markdown report、PowerShell 安装/运行/计划任务脚本

### 当前验证结果

```text
python -m unittest discover -s tests -v
Ran 27 tests ... OK

python -m compileall -q src tests
exit 0

python -m ruff check src tests --select F,I
All checks passed

isolated venv: pip install -e . + spot-agent --help
exit 0

quick_validate.py skills/<each skill>
8 / 8 Skill is valid
```

端到端 Fake Testnet 测试已覆盖：权限预检、市场分析、干跑、Risk Gate、6 个唯一订单提交、状态与 Journal 写入。公共 Binance smoke test 已读取实时 BTCUSDT 价格和 filters。

## 不能在无用户密钥条件下声称完成的外部验收

- 用户 Testnet 账户的真实签名、余额、commission 和订单 Test endpoint
- Testnet 真实下单/撤单/部分成交/重启三方对账
- 用户主网账号是否有 Sub Accounts 功能
- 用户实际 API Key 权限与公网 IP 白名单
- $10 Mainnet Smoke Test
- $100 数月长期策略结果

这些不是代码缺口，而是需要用户自己的 Binance 账户状态、人工授权和真实运行时间。未完成之前，`policies/constitution.json` 默认保持 `live_trading_enabled=false`。

## 已知限制

- 只支持 Binance Global 风格的 HMAC Spot REST API；不支持 Binance.US、Binance TR 或其他地区独立平台。
- 本地哈希链可发现内容修改、插入和重排；同一主机完全失陷时，攻击者仍可能同时修改数据库与文件。主网长期运行应把每日 journal hash 复制到外部只写存储。
- 当前用轮询对账而不是 User Data WebSocket；V1 低频足够，但成交发现延迟取决于周期。
- Regime 规则有测试但没有数月标签集，不能称为已证明有效。
- 日内损失按账户 BTC+USDT mark-to-market 近似；长期报告尚不能替代交易所税务/财务报表。
- 七天 activation 只证明本机配置未被简单篡改，不是硬件安全模块。

## 放行顺序

`Simulation → Testnet order-test → Testnet lifecycle → $10 Stage 1 → 数月 $100 Stage 2`

任何阶段失败都回到前一阶段，不自动增加资金，不启用转账或提款权限。
