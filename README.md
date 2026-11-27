# node-pool

从 [@Darlene-Alderson-FSOCIETY](https://gist.github.com/Darlene-Alderson-FSOCIETY) 的三个 gist 自动汇总，统一改写成标准分享链接，并生成 Clash / sing-box / Surge 配置。
由 GitHub Actions 每 6 小时同步一次。

- 更新时间：2026-11-27 16:40 UTC
- 节点总数：**319**（去重后，单源 409 条）
- 协议：vless 267, hysteria2 30, ss 15, vmess 5, trojan 2
- 安全层：reality 221, tls 75, plain 15, none 8

## 文件

| 文件 | 用途 |
| --- | --- |
| `sub/nodes.txt` | 标准分享链接，一行一条 |
| `sub/v2ray.txt` | 上面那份的 Base64（v2rayN / Shadowrocket 订阅格式） |
| `sub/clash.yaml` | mihomo / Clash Meta（REALITY 用 `reality-opts`） |
| `sub/singbox.json` | sing-box 1.10+ |
| `sub/surge.conf` | Surge 6（VLESS/REALITY 需 iOS 6.0.0+） |

## 订阅地址

```
https://raw.githubusercontent.com/lylywayr/node-pool/main/sub/v2ray.txt
https://raw.githubusercontent.com/lylywayr/node-pool/main/sub/clash.yaml
https://raw.githubusercontent.com/lylywayr/node-pool/main/sub/singbox.json
```

## 地区分布

| 地区 | 数量 |
| --- | --- |
| RU | 123 |
| US | 35 |
| CA | 17 |
| DE | 17 |
| FI | 14 |
| NL | 12 |
| FR | 11 |
| GB | 10 |
| CH | 9 |
| ES | 8 |
| IT | 6 |
| PL | 6 |
| SE | 6 |
| SG | 6 |
| AU | 5 |

## 说明

节点来自公开 Telegram 频道 @RE_s_B 的镜像，属公共共享资源，随时可能失效；不要在上面登录重要账号。
配置为机器生成，`sync.py` 是唯一源文件。
