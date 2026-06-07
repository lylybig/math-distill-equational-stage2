# Weekly Reports

> 每周一个目录 `YYYY-Www/`，里面每人一个 `<pinyin>.md`，外加组长一个 `_lead.md`。
> 每人编辑自己那份，撞编辑零摩擦。

## 目录结构

```
docs/weekly/
├── README.md                  ← 本文件
├── _template/                 ← 模板, 复制此目录起新一周
│   ├── _lead.md
│   └── _member.md
├── 2026-W22/
│   ├── _lead.md               ← 组长写
│   ├── wubing.md              ← 吴兵写
│   ├── zhangkang.md           ← 张康写
│   └── yanliang.md            ← 严亮写
├── 2026-W23/
│   ├── _lead.md
│   ├── ...
```

## 起新一周

```bash
# 在 main 上 (公共改动走 PR)
git switch main && git pull
git checkout -b feat/weekly-2026-W22
WEEK=2026-W22
mkdir docs/weekly/$WEEK
cp docs/weekly/_template/_lead.md docs/weekly/$WEEK/_lead.md
cp docs/weekly/_template/_member.md docs/weekly/$WEEK/wubing.md
cp docs/weekly/_template/_member.md docs/weekly/$WEEK/zhangkang.md
cp docs/weekly/_template/_member.md docs/weekly/$WEEK/yanliang.md
git add docs/weekly/$WEEK
git commit -m "weekly: open $WEEK"
git push -u origin HEAD
gh pr create --title "weekly: open $WEEK" --body "起 $WEEK 周报骨架, 每人 fill 自己那份"
```

组长开骨架的 PR 合并后, 每人各自走小 PR 填自己那份。

## 每人填周报

```bash
git switch main && git pull
git checkout -b feat/weekly-2026-W22-<你>
# 编辑 docs/weekly/2026-W22/<你>.md
git add docs/weekly/2026-W22/<你>.md
git commit -m "weekly: 2026-W22 <你>"
git push -u origin HEAD
gh pr create --title "weekly: 2026-W22 <你>"
```


