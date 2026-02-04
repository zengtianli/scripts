---
name: dev-lessons
description: 开发部经验教训。踩坑记录、最佳实践、检查清单。当开发脚本遇到问题或需要避坑时触发。
---

# 开发部经验教训

> 记录开发过程中的踩坑经验，避免重复犯错

## 核心原则：数据处理必须闭环

### 问题背景

**时间**：2025-12-15  
**场景**：开发 `backup.sh` 的 diff 功能  
**问题**：边处理边输出，大数据量（19000+ 行）时管道断开（SIGPIPE），导致终端输出不完整

### 错误做法 ❌

```bash
# 边处理边输出 - 管道链式处理
restic diff ... | grep ... | while read line; do
    echo "$line"        # 输出到终端
    echo "$line" >> file  # 同时写文件
done
```

### 正确做法 ✅

```bash
# 先存后显 - 分离数据处理和展示

# 1. 数据采集 → 临时文件
restic diff ... > /tmp/diff_raw.txt

# 2. 数据处理 → 保存到最终文件（确保完整）
generate_report > ~/.backup-reports/diff-xxx.txt

# 3. 从文件读取 → 显示到终端
head -50 ~/.backup-reports/diff-xxx.txt
echo "完整报告: ~/.backup-reports/diff-xxx.txt"
```

## 脚本命名规范（2025-12-16）

### 错误做法 ❌

```bash
# 在 shell 配置文件中定义函数
backup () { ... }

# 无后缀脚本文件
~/scripts/backup
```

### 正确做法 ✅

```bash
# 脚本文件必须带后缀
~/useful_scripts/system/backup/backup.sh

# 如需快捷使用，通过软链接或别名
ln -s ~/useful_scripts/system/backup/backup.sh ~/bin/backup.sh
alias backup='bash ~/useful_scripts/system/backup/backup.sh'
```

## 功能只增不删原则（2025-12-17）

### 问题

用户要求"增加数据量显示"，错误理解为"把目录数目替换成数据量"

### 原则

- **只增不删**：用户要加功能就加，不要动原有功能
- **不擅自替换**：除非用户明确说"把 A 换成 B"
- **保守修改**：不确定时保留原有功能

## 检查清单

### 数据输出功能

- [ ] 数据量大时会不会有问题？
- [ ] 管道断开时数据会丢失吗？
- [ ] 重要数据是否先持久化？
- [ ] 用户能否事后查看完整结果？

### 界面修改

- [ ] 用户是要"增加"还是"替换"？
- [ ] 原有功能是否还需要保留？
- [ ] 这个修改会不会影响用户习惯？
- [ ] 不确定时，是否应该先问？

## 经验总结

| 错误模式 | 正确模式 |
|---------|---------|
| 边处理边输出 | 先存后显 |
| 管道链式处理 | 中间结果存文件 |
| 出错打补丁 | 找根本原因重构 |
| 只考虑正常情况 | 考虑异常场景 |
| 治标不治本 | 架构层面解决 |
