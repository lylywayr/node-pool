# node-pool

从 [@Darlene-Alderson-FSOCIETY](https://gist.github.com/Darlene-Alderson-FSOCIETY) 的三个 gist 自动汇总，统一改写成标准分享链接，并生成 Clash / sing-box / Surge 配置。
由 GitHub Actions 每 6 小时同步一次。

- 更新时间：2026-11-28 15:31 UTC
- 节点总数：**381**（去重后，单源 480 条）
- 协议：vless 299, hysteria2 44, trojan 19, ss 15, vmess 4
- 安全层：reality 235, tls 121, plain 15, none 10

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
| RU | 130 |
| US | 42 |
| JP | 24 |
| DE | 19 |
| CA | 18 |
| FI | 18 |
| GB | 13 |
| NL | 11 |
| PL | 10 |
| CH | 9 |
| ES | 9 |
| FR | 8 |
| SG | 7 |
| AU | 6 |
| IT | 6 |

## 说明

节点来自公开 Telegram 频道 @RE_s_B 的镜像，属公共共享资源，随时可能失效；不要在上面登录重要账号。
配置为机器生成，`sync.py` 是唯一源文件。
