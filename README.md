# node-pool

从 [@Darlene-Alderson-FSOCIETY](https://gist.github.com/Darlene-Alderson-FSOCIETY) 的三个 gist 自动汇总，统一改写成标准分享链接，并生成 Clash / sing-box / Surge 配置。
由 GitHub Actions 每 6 小时同步一次。

- 更新时间：2026-11-25 17:14 UTC
- 节点总数：**294**（去重后，单源 374 条）
- 协议：vless 245, hysteria2 22, ss 15, vmess 7, trojan 5
- 安全层：reality 203, tls 67, plain 15, none 9

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
| RU | 117 |
| US | 36 |
| DE | 17 |
| FI | 15 |
| GB | 12 |
| FR | 9 |
| CH | 8 |
| NL | 8 |
| ES | 7 |
| UA | 7 |
| SE | 6 |
| AU | 5 |
| PL | 5 |
| CA | 4 |
| IT | 4 |

## 说明

节点来自公开 Telegram 频道 @RE_s_B 的镜像，属公共共享资源，随时可能失效；不要在上面登录重要账号。
配置为机器生成，`sync.py` 是唯一源文件。
