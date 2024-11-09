一款适用于Endstone插件加载器的玩家行为记录查询插件。


# 功能介绍

## 行为记录

天眼插件使用endstone的事件API进行行为事件的记录，可以对以下行为事件进行记录：

### 容器交互和其它交互行为事件

玩家对箱子、陷阱箱、潜影箱、末影箱、木桶、熔炉、高炉、漏斗、发射器、投掷器的交互行为；玩家手持打火石、岩浆桶、火焰弹、水桶（包括生物水桶）、细雪桶对任何方块的交互行为；玩家手持桶对水、岩浆、细雪的交互行为；玩家对床、重生锚的任何交互行为。

### 方块破坏行为事件

在仅记录人工方块配置下，对玩家直接造成的全部人工方块（非自然方块）和部分自然方块的破坏行为（踩踏农田无法记录）进行记录；在关闭仅记录人工方块配置下，对玩家直接造成的全部方块破坏行为（踩踏农田无法记录）进行记录。

### 实体受击事件

在仅记录重要生物配置下，仅对马、猪、狼、猫、嗅探兽、鹦鹉、驴、骡子、村民的受击事件进行记录（不是玩家打的也会记录）；在关闭仅记录重要生物配置下，会对全部实体的受击事件进行记录（玩家被实体攻击、实体被非玩家攻击也会记录）。

### 方块放置事件记录

插件将对全部玩家直接实行的方块放置行为事件进行记录。

## 玩家信息显示和封禁功能

### 玩家加服信息显示

天眼插件支持玩家加服信息显示和封禁功能。当玩家加入服务器时，将显示玩家的系统名称和设备ID。

### 封禁功能&防刷屏功能

插件可以通过封禁玩家名阻止玩家进入服务器，还支持通过封禁设备ID将设备拉入封禁名单，使得使用该设备（设备ID不变）的任何玩家都无法进入服务器。当要封禁的玩家仍在服务器中时，使用命令封禁玩家设备ID或通过控制台封禁玩家名只能将玩家加入封禁名单，无法直接踢出玩家。
当玩家在服务器内短时间发送大量消息（10秒内6条消息）时，将被自动封禁；当玩家在服务器内短时间发送大量命令（10秒内12条命令）时将被自动封禁。需要联系管理员才能解除封禁

# 安装&配置&使用方法

## 安装endstone

这一步请参考[endstone官方文档](https://endstone.dev/latest/getting-started/installation/)。

## 安装天眼插件

在[release](https://github.com/yuhangle/Endstone_TianyanPlugin/releases)处下载最新版本的插件，放在服务端目录的plugins目录下，运行服务端即可使用。

## 配置天眼插件

运行天眼插件后，将在服务端目录的plugins目录下生成tianyan_data文件夹，里面有插件的配置文件config.json，打开config.json，里面是默认配置

```shell
{"是否记录自然方块": false, "是否记录人工方块": true,"是否仅记录重要生物": true}
```

插件默认配置不记录大部分自然方块的破坏行为事件，仅记录大部分人工方块的破坏行为事件，仅记录部分重要生物的受击事件。如果需要记录全部方块的破坏行为事件，请将“是否记录自然方块”后的“false”修改为“true”；如果需要记录全部生物的受击事件，请将“是否仅记录重要生物”后的“false”修改为“true”。

## 插件命令使用方法

天眼命令使用方法

使用 /tyc 命令查询容器交互记录及其它交互记录 格式:

```shell
/tyc x坐标 y坐标 z坐标 时间（单位：小时） 半径
```

使用 /tyb 命令查询方块破坏记录 格式:

```shell
/tyb x坐标 y坐标 z坐标 时间（单位：小时） 半径
```

使用 /tya 命令查询生物受击记录 格式:

```shell
/tya x坐标 y坐标 z坐标 时间（单位：小时） 半径
```

使用 /typ 命令查询方块放置记录 格式:

```shell
/typ x坐标 y坐标 z坐标 时间（单位：小时） 半径
```

使用 /tys 命令搜索关键词 格式:

```shell
/tys 搜索类型 行为类型 搜索关键词 时间（单位：小时）
```

搜索类型:player action object(玩家或行为实施者 行为 被实施行为的对象) 行为类型:jh ph st fz(交互 破坏 实体受击 放置) 搜索关键词:玩家名或行为实施者名 交互 破坏 攻击 放置 被实施行为的对象名。关键词可以为玩家名、行为名、行为实施者名、被实施行为的对象名，其中行为名共以下几种：交互、破坏、攻击、放置；被实施行为的对象名除了以下类型为中文值，其余皆为游戏中的ID：箱子、陷阱箱、潜影盒、末影箱、木桶、漏斗、发射器、投掷器、熔炉、高炉。

使用/ban 命令将一名玩家加入黑名单(当目标玩家在线时添加黑名单无法直接踢出，请使用其它方法踢出该玩家) 格式:

```shell
/ban 玩家名 理由(选填)
```

使用/unban 命令将一名玩家移出黑名单 格式:

```shell
/unban 玩家名
```

使用/banlist命令列出所有被加入黑名单的玩家名

```shell
/banlist 
```

使用/banid 命令将一名玩家的设备加入黑名单(当目标玩家设备在线时添加黑名单无法直接踢出，请使用其它方法踢出该玩家) 格式:

```shell
/banid 设备ID
```

使用/unbanid 命令将一名玩家的设备移出黑名单 格式:

```shell
/unban 设备ID
```

使用/banlist 命令列出所有被加入黑名单的玩家的设备ID

```shell
/banlist
```

使用/tyclean 命令备份并清理超过两个星期的数据

```shell
/tyclean
```

# 修改&打包

确保您的python环境中安装了endstone和pipx

克隆代码
```shell
git clone https://github.com/yuhangle/Endstone_TianyanPlugin.git
```

进入代码目录

```shell
cd Endstone_TianyanPlugin
```

打包插件
```shell
pipx run build --wheel
```