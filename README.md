# ict-trading-model

一个用于 ICT / SMC 图表分析与交易结构验证的 Agent Skill。

它不会因为图上出现一个 FVG 或一根反向 K 线就直接给出交易结论，而是按完整证据链检查：

```text
高周期方向
→ 流动性目标
→ Premium / Discount 位置
→ 流动性扫荡
→ 位移与严格 FVG
→ 收盘结构突破
→ OB / FVG / Breaker / OTE 回踩
→ 失效位与目标
→ 风险回报比
```

Skill 只提供分析和条件计划，不会自动执行交易。

## 安装

```bash
npx skills add https://github.com/carreypro/ict-trading-model --skill ict-trading-model
```

安装后可以显式调用：

```text
使用 $ict-trading-model 分析这张图。
```

提到 ICT、SMC、流动性扫荡、FVG、OB、Breaker、OTE、MSS 或 BOS 时，也可以自动触发。

## 用户可以怎么使用

### 1. 上传图表复盘

```text
使用 $ict-trading-model 复盘这张图。

请按时间顺序标出：
- 高周期方向
- BSL 和 SSL
- 流动性扫荡
- 位移与 FVG
- MSS / BOS
- 有效 OB 或 Breaker
- 理想回踩、失效位和目标
- 哪些机会成立，哪些属于假信号
```

截图只能支持视觉判断。无法从图片精确确认的 OHLC、FVG 边界和时间信息会被标记为 `unverified`。

### 2. 分析实时市场

```text
使用 $ict-trading-model 分析 BTC-USDT-SWAP。

方向周期：4H
结构周期：15m
执行周期：5m

请给出 confirmed、developing、invalidated 或 no-trade，
并列出每项证据。不要执行交易。
```

实时请求应先获取最新行情，并说明交易所、数据时间和最后一根已收盘 K 线。

### 3. 验证用户自己的判断

```text
我认为这里扫了前高，并形成空头 MSS 和 bearish FVG。

使用 $ict-trading-model 严格检查：
- 前高是否属于有效流动性
- 是扫荡还是有效突破
- 是否存在真正的空头位移
- MSS 是否为收盘确认
- FVG 是否满足三根 K 线定义
- OB 是否确实造成了结构突破
- 当前是否已经错过入场
```

Skill 会检查用户判断，不会为了匹配预期而强行确认形态。

### 4. 分析 OHLCV 文件

```text
使用 $ict-trading-model 分析：
/absolute/path/to/candles.json

扫描多头和空头结构，并输出最近的候选机会。
```

也可以直接运行扫描器：

```bash
python3 scripts/ict_scan.py \
  --input /absolute/path/to/candles.json \
  --direction auto \
  --swing-width 2 \
  --minimum-rr 2
```

支持两种 K 线格式。

对象格式：

```json
{
  "meta": {
    "instrument": "BTC-USDT-SWAP",
    "timeframe": "5m"
  },
  "candles": [
    {
      "timestamp": "2026-10-10T02:00:00Z",
      "open": 100,
      "high": 102,
      "low": 99,
      "close": 101,
      "volume": 1234
    }
  ]
}
```

数组格式：

```json
[
  [1791597600000, 100, 102, 99, 101, 1234]
]
```

实际扫描至少需要 10 根 K 线。时间倒序的数据会自动按时间重新排序。

## Skill 使用流程

### 第一步：确认数据条件

确认标的、交易场所、K 线周期、持仓周期、数据时间和当前 K 线是否已经收盘。禁止把示例数据或旧截图当作实时行情。

### 第二步：建立高周期方向

判断高周期订单流、当前 dealing range 和主要外部流动性。高周期负责方向，不负责精确入场。

### 第三步：绘制流动性地图

标记：

- 旧高、旧低；
- EQH、EQL；
- 前日和前周高低；
- 交易时段高低；
- 内部摆动点与失衡。

### 第四步：检查价格位置

在明确的 dealing range 内判断：

- Premium；
- Equilibrium；
- Discount；
- 下一个可能的流动性目标；
- 通往目标的阻碍。

空头优先在 Premium 寻找机会，多头优先在 Discount 寻找机会。

### 第五步：等待流动性事件

多头模型需要有效 SSL 扫荡；空头模型需要有效 BSL 扫荡。只有突破而没有拒绝，不应自动称为扫荡。

### 第六步：验证位移和结构

位移应表现为明显扩张、较大的实体、有效收盘和严格 FVG。

- 反转结构重点检查 MSS；
- 趋势延续重点检查 BOS；
- 只有影线穿越不算收盘结构确认。

### 第七步：寻找执行区域

识别真正造成位移和结构突破的 OB，并检查是否与以下区域重合：

- 严格 FVG；
- Breaker；
- OTE；
- Premium / Discount 正确一侧。

OTE 是位移区间 `0.62–0.79` 的回撤区域，`0.705` 是中心位置，不属于 OB 自身属性。

### 第八步：验证风险

计划必须包含：

- 精确触发条件；
- 结构失效位；
- 对侧流动性目标；
- 至少 `1:2` 的净风险回报比；
- 时间失效或 no-trade 条件。

### 第九步：输出唯一状态

| 状态 | 含义 |
|---|---|
| `confirmed` | 必要条件全部通过 |
| `developing` | 叙事有效，但仍等待结构突破、回踩或其他必要条件 |
| `invalidated` | 结构失效位已经被突破 |
| `no-trade` | 位置太晚、证据冲突、数据不足或风险回报比不合格 |

## 完整使用示例

用户输入：

```text
使用 $ict-trading-model 分析我上传的 ETH 15 分钟图。

我认为价格先扫了前高，然后向下跌破最近的摆动低。
请不要直接认同我，严格检查：

1. 前高是否构成有效 BSL；
2. 扫高后是否有空头位移和严格 bearish FVG；
3. 摆动低是否被实体收盘跌破；
4. 哪一根上涨 K 线有资格成为 bearish OB；
5. OB、FVG 和 OTE 是否重合；
6. 当前属于 confirmed、developing、invalidated 还是 no-trade；
7. 如果仍在 developing，明确还需要等待什么。

不要执行交易。
```

预期输出结构：

```text
状态：developing
方向：候选空头

已确认：
- 前高上方流动性已被触及并拒绝
- 出现向下扩张

尚未确认：
- 最近摆动低只有影线跌破，没有收盘确认
- bearish FVG 边界无法从截图精确读取

下一步条件：
- 等待 15m 收盘跌破摆动低
- 确认位移形成严格 FVG
- 等价格回踩 Premium 一侧的 FVG / OB

失效条件：
- 价格重新收盘站上扫荡高点

结论：目前不能标记 confirmed，也不应提前追空。
```

这个示例展示了核心原则：证据不足时输出 `developing`，而不是为了给出交易机会而补全缺失条件。

## 扫描器输出

`scripts/ict_scan.py` 会检测：

- 摆动高低点；
- 严格 FVG；
- BSL / SSL 扫荡；
- 位移强度；
- 收盘结构突破；
- dealing range 与 OTE；
- 回踩状态；
- 候选目标和毛风险回报比。

扫描器输出的 `mechanical_status` 不是最终交易结论。高周期叙事、关键流动性的有效性、事件风险和真实交易成本仍需人工确认。

## 限制与风险

- ICT / SMC 标签属于价格行为分析框架，不是机构活动的直接证明。
- 截图无法替代完整 OHLCV 数据。
- 扫描器计算的是毛风险回报比，不包含手续费、点差和滑点。
- 反向合约、期权或特殊合约需要单独计算单位和风险。
- 本项目用于教育和研究，不构成投资建议。

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/ict_scan.py
```

## License

MIT
