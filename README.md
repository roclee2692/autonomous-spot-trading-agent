# Autonomous Spot Trading Agent V1

面向 Binance BTC/USDT 的低频、可解释、Constitution-first 现货交易 Harness。

## 成品能力

- Simulation、Binance Spot Testnet、Binance Spot Mainnet 三环境硬隔离
- Windows Credential Manager 本机密钥存储；配置、日志和数据库不保存 Secret
- 启动时读取交易规则、账户余额、账户实际手续费与 API 权限
- 主网强制：IP 白名单、Reading、Spot Trading；提款、内部转账、Margin、Futures、Options、Portfolio Margin 必须关闭
- 只允许 `BTCUSDT + SPOT + LIMIT_MAKER`
- `UPTREND / DOWNTREND / RANGE / BREAKOUT / PANIC / UNCERTAIN`
- 只有 RANGE 允许低频 Grid；其他状态停止新 Grid，Panic/Uncertain/Kill Switch 撤销 Agent 自有挂单
- $10 Stage 1：最多一个真实订单
- $100 Stage 2：3 Buy + 3 Sell，每单最多 $10，$20 BTC Core，$20 USDT Reserve
- 间距为 `max(round-trip cost × 3, volatility spacing, 0.6%)`，上限 2.5%
- 实际成交数量、手续费资产、部分成交和 rounding buffer 后再生成配对单
- SQLite 持久状态、不可修改 Thesis/Fill trigger、远端订单与成交启动对账
- 写请求超时绝不自动重试；使用 `clientOrderId` 查询未知结果
- 歧义订单只能用 `resolve-unknown` 查询，并在交易所返回不存在时人工精确确认后解锁
- SHA-256 哈希链 Journal、Kill Switch、七天 Mainnet activation、周期报告

## 先读

完整的 Binance 账号、API Key、子账户和转账步骤见：

[BINANCE_SETUP_ZH.md](BINANCE_SETUP_ZH.md)

API Key **不是从本地自动提取**。它必须在 Binance 网站或 Spot Testnet 创建，然后用项目命令存入当前 Windows 用户的 Credential Manager。不要把 Key 或 Secret 发到聊天、邮件、截图或 Git 仓库。

## 安装

```powershell
cd <项目目录>
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
.\.venv\Scripts\python.exe -m spot_agent --help
```

## 无密钥体验

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m spot_agent market
python -m spot_agent plan-grid --daily-volatility 0.03 --maker-fee 0.001
python -m spot_agent demo --price 76000
python -m unittest discover -s tests -v
```

## Testnet 最短路径

```powershell
.\.venv\Scripts\python.exe -m spot_agent credentials set testnet
.\.venv\Scripts\python.exe -m spot_agent preflight --config .\config.testnet.toml
.\.venv\Scripts\python.exe -m spot_agent order-test --config .\config.testnet.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.testnet.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.testnet.toml --execute
```

不加 `--execute` 永远不会提交订单。Mainnet 还需要 Constitution flag、主网权限预检和七天 activation 三重通过。

## 紧急停止

```powershell
.\.venv\Scripts\python.exe -m spot_agent kill-switch on --config .\config.stage2-live.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.stage2-live.toml --execute
```

这会阻止新单并尝试撤销本 Agent 创建的已知挂单。若电脑或网络异常，立即在 Binance 网页端禁用/删除 API Key，并手工撤单。

## 当前验收边界

代码、离线故障注入、公共行情 smoke test 已验收。需要用户自己的 Testnet Key 才能完成 Binance 账户侧验收；需要用户本人完成 KYC、地区合规、子账户创建、内部转账和主网 API 安全设置后，才可能进入 $10 Stage 1。详见 [EVALUATION_HANDOFF.md](EVALUATION_HANDOFF.md)。
