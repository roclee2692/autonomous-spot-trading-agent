# Binance 账号、API Key、子账户与资金接入

核验日期：2026-08-23。Binance 页面名称会随地区和版本变化；只从你自己保存的 Binance 官方书签进入，并遵守所在地法律、Binance 条款和账户限制。

## 先回答你的问题

### API Key 要从本地取吗？

不是。

1. 你先在 Binance Spot Testnet 或 Binance 账号网页里**新建** API Key。
2. Binance 返回 `API Key` 和 `Secret Key`。Secret 通常只完整显示一次。
3. 回到这台 Windows 电脑运行项目的 `credentials set` 命令，在隐藏输入框中粘贴。
4. 项目把它保存到当前 Windows 用户的 Credential Manager。TOML、SQLite、Journal、报告和 Git 文件都不保存 Secret。

不要把密钥发给 Codex/ChatGPT，不要写进 `.env`、代码、截图或聊天。电脑中毒时 Windows 凭证也可能被窃取，所以 IP 白名单仍然必须开启。

## A. 先接 Spot Testnet

1. 打开官方 Spot Testnet：<https://testnet.binance.vision/>。
2. 按页面支持的登录方式登录。当前官方说明使用 GitHub 登录并签发测试 API Key/Secret。
3. Testnet 只含虚拟资产，不需要从主账户转钱。
4. 在项目目录安装：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

5. 保存测试密钥。输入不会显示：

```powershell
.\.venv\Scripts\python.exe -m spot_agent credentials set testnet
```

6. 依次验证：

```powershell
.\.venv\Scripts\python.exe -m spot_agent credentials status testnet
.\.venv\Scripts\python.exe -m spot_agent preflight --config .\config.testnet.toml
.\.venv\Scripts\python.exe -m spot_agent order-test --config .\config.testnet.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.testnet.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.testnet.toml --execute
```

`order-test` 调用 Binance 的测试下单端点，不会留下订单；最后一条才会在 Testnet 创建虚拟订单。

至少完成：下单、查询、部分/完整成交、撤单、进程重启、断网后对账、Kill Switch 和未知提交结果演练。不能只看到一次成功就进入主网。

如果写请求断网，订单会停在 `UNKNOWN`，系统不会自动重下。先去 Binance 网页按 `clientOrderId` 核对，再运行：

```powershell
.\.venv\Scripts\python.exe -m spot_agent resolve-unknown <clientOrderId> --config .\config.testnet.toml
```

程序会再次查询交易所。只有 Binance 返回订单不存在且你输入包含该 ID 的精确确认语句时，本地才解除歧义锁；它永远不会在这个命令中重新下单。

## B. 建立专用 Binance 子账户

强烈建议主账户只做管理，不把主账户交易 Key 交给 Agent。

1. 登录 Binance 主账户。
2. 在 Profile / Account 中寻找 `Sub Accounts`。界面文字可能是“子账户”“账户管理”或“Sub-Account”。
3. 新建一个用途明确的子账户，例如 `btc-grid-v1`。
4. 不要为它开通 Margin、Futures、Options 或 Portfolio Margin。
5. 如果你的页面没有 Sub Accounts，说明当前账号等级、账号类型、地区或产品版本可能不支持。联系 Binance 官方客服确认；不要用第二身份或规避地区限制的方法绕过。

Binance 当前也提供主账户 API 创建 virtual sub-account，但本项目**故意不实现**：创建子账户和资金调拨必须由人从网页完成。

## C. 先只转 $10 做 Stage 1

在 Binance 网页的 Sub Accounts / Asset Management 中：

1. 选择从 `Main Account Spot` 转到 `btc-grid-v1 Spot`。
2. 资产选择 `USDT`。
3. 金额先转 `10 USDT`。
4. 核对方向必须是主账户 → 子账户；不要转到 Margin/Futures wallet。

这通常是 Binance 内部账本转移，不是链上提款。仍然应由你手工完成并核对。交易 Agent 的 API Key 不需要、也不得拥有 `Internal Transfer` 或 `Universal Transfer` 权限。

## D. 在专用子账户创建 Mainnet API Key

在子账户的 API Management 中：

1. 点击 `Create API`，选择 Binance 当前提供的 `System generated` / HMAC Key。
2. 完成 2FA 安全验证。
3. 复制 API Key 和 Secret Key；Secret 通常只显示一次。
4. 权限按下面配置：

| 设置 | 必须值 |
|---|---|
| Enable Reading | 开启 |
| Restrict access to trusted IPs | 开启，并只填运行这台机器/服务器的固定公网 IP |
| Enable Spot & Margin Trading | 开启；Binance UI 用这个组合开关授权 Spot API |
| Enable Margin | 关闭 |
| Enable Futures | 关闭 |
| Enable Vanilla Options | 关闭 |
| Portfolio Margin | 关闭 |
| Enable Withdrawals | **关闭** |
| Enable Internal Transfer | **关闭** |
| Permits Universal Transfer | **关闭** |
| Symbol Whitelist | 如果页面提供，限制为 `BTCUSDT` |

家庭宽带公网 IP 如果经常变化，IP 白名单会导致程序停止，这是安全的失败方式。使用固定公网 IP 的专用 Windows 主机/VPS，或者每次 IP 变化后由你手工更新白名单；不要为了方便关闭 IP restriction。

5. 本机保存 Mainnet Key：

```powershell
.\.venv\Scripts\python.exe -m spot_agent credentials set live
.\.venv\Scripts\python.exe -m spot_agent credentials status live
```

6. 权限预检和无成交测试：

```powershell
.\.venv\Scripts\python.exe -m spot_agent preflight --config .\config.stage1-live.toml
.\.venv\Scripts\python.exe -m spot_agent order-test --config .\config.stage1-live.toml
```

程序会读取 Binance `apiRestrictions`。任一危险权限为开、IP 未限制、账户不能交易或手续费高于配置上限，都会 `NO_TRADE`。

## E. Stage 1：$10 Mainnet Smoke Test

只有 Testnet 验收后：

1. 人工审阅 `EVALUATION_HANDOFF.md`。
2. 打开 `policies/constitution.json`，只把 `live_trading_enabled` 从 `false` 改为 `true`。
3. 创建七天、本机、Stage 和资金上限绑定的 activation：

```powershell
.\.venv\Scripts\python.exe -m spot_agent arm-live --config .\config.stage1-live.toml
```

4. 先干跑：

```powershell
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.stage1-live.toml
```

5. 确认输出只有一个、约 $9.x 的 `LIMIT_MAKER` 后才执行：

```powershell
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.stage1-live.toml --execute
```

Stage 1 同时最多一个订单。它只验证真实手续费、数量、撤单/成交、重启对账和余额，不评价策略利润。

## F. Stage 2：调整为总计 $100

只有 Stage 1 一个完整买卖生命周期、异常恢复和日志全部正确后：

1. 在子账户网页中把总资产补到约 `$100`，不是额外再给 $100。
2. 调整为约 `$50 BTC + $50 USDT`。可以由你在子账户 Spot 页面手工买约 $50 BTC。
3. 不要留下 BNB 或其他币。V1 主网预检发现 BTC/USDT 之外的非零资产会停止，避免手续费资产和核算口径漂移。
4. 使用 Stage 2 配置重新 activation：

```powershell
.\.venv\Scripts\python.exe -m spot_agent preflight --config .\config.stage2-live.toml
.\.venv\Scripts\python.exe -m spot_agent arm-live --config .\config.stage2-live.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.stage2-live.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.stage2-live.toml --execute
```

Stage 2 最多 6 单：3 Buy + 3 Sell；每单最多 $10；保留 $20 BTC Core 和 $20 USDT Reserve。

## G. 低频自动运行

完成多次手工 `run-once` 核对后，可注册当前 Windows 用户下每 4 小时运行一次的计划任务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\register-stage2-task.ps1
```

Credential Manager 凭证属于当前 Windows 用户，所以计划任务必须使用同一个用户运行，不能勾选未知服务账户。

停止计划任务：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\unregister-stage2-task.ps1
```

## H. 停止、撤权和把钱转回

1. 激活 Kill Switch 并运行一次，让 Agent 撤销自己已知的挂单：

```powershell
.\.venv\Scripts\python.exe -m spot_agent kill-switch on --config .\config.stage2-live.toml
.\.venv\Scripts\python.exe -m spot_agent run-once --config .\config.stage2-live.toml --execute
```

2. 在 Binance 网页检查是否还有挂单。
3. 在 API Management 禁用或删除该 API Key。
4. 由你在 Sub Accounts / Asset Management 手工把 BTC/USDT 从子账户 Spot 转回主账户 Spot。
5. 删除本机密钥：

```powershell
.\.venv\Scripts\python.exe -m spot_agent credentials delete live
```

Agent 没有转账和提款能力，所以“转回主账户”永远是人工网页操作。
