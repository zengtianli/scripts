import { NextRequest, NextResponse } from 'next/server'

interface Script {
  id: string
  name: string
  title: string
  description: string
  type: string
  function: string
  platform: string
  tags: string[]
}

export async function POST(request: NextRequest) {
  try {
    const { message, scripts } = await request.json() as {
      message: string
      scripts: Script[]
    }

    if (!message) {
      return NextResponse.json({ error: '缺少消息内容' }, { status: 400 })
    }

    // 简单的关键词匹配 AI 助手
    const reply = generateReply(message, scripts)

    return NextResponse.json({ reply })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

function generateReply(message: string, scripts: Script[]): string {
  const q = message.toLowerCase()

  // 查找相关脚本
  const matchedScripts = scripts.filter(s => {
    const matchName = s.name.toLowerCase().includes(q)
    const matchTitle = s.title.toLowerCase().includes(q)
    const matchDesc = s.description.toLowerCase().includes(q)
    const matchType = s.type.toLowerCase().includes(q)
    const matchTags = s.tags.some(t => q.includes(t.toLowerCase()))
    return matchName || matchTitle || matchDesc || matchType || matchTags
  })

  // 类型查询
  const typeKeywords: Record<string, string[]> = {
    'docx': ['word', 'docx', '文档', 'word文档'],
    'xlsx': ['excel', 'xlsx', '表格', 'excel表格'],
    'csv': ['csv', '数据'],
    'md': ['markdown', 'md'],
    'pptx': ['ppt', 'pptx', 'powerpoint', '幻灯片'],
    'pdf': ['pdf'],
    'yabai': ['yabai', '窗口', '平铺'],
    'clashx': ['clash', 'clashx', '代理', 'vpn'],
  }

  for (const [type, keywords] of Object.entries(typeKeywords)) {
    if (keywords.some(k => q.includes(k))) {
      const typeScripts = scripts.filter(s => s.type === type)
      if (typeScripts.length > 0) {
        const list = typeScripts.map(s => `• ${s.title}: ${s.description || s.name}`).join('\n')
        return `找到 ${typeScripts.length} 个${type.toUpperCase()}相关脚本：\n\n${list}`
      }
    }
  }

  // 功能查询
  const funcKeywords: Record<string, string[]> = {
    'convert': ['转换', '转成', '转为', 'convert'],
    'format': ['格式化', '格式', '样式', 'format'],
    'analyze': ['分析', '提取', '拆分', '合并', 'analyze'],
    'automation': ['自动化', '自动', 'automation'],
  }

  for (const [func, keywords] of Object.entries(funcKeywords)) {
    if (keywords.some(k => q.includes(k))) {
      const funcScripts = scripts.filter(s => s.function === func)
      if (funcScripts.length > 0) {
        const list = funcScripts.map(s => `• ${s.title}: ${s.description || s.name}`).join('\n')
        return `找到 ${funcScripts.length} 个${func}功能脚本：\n\n${list}`
      }
    }
  }

  // 平台查询
  if (q.includes('raycast')) {
    const raycastScripts = scripts.filter(s => s.platform === 'raycast')
    return `共有 ${raycastScripts.length} 个 Raycast 脚本。\n\n可以按类型筛选查看具体脚本。`
  }

  if (q.includes('cli') || q.includes('命令行')) {
    const cliScripts = scripts.filter(s => s.platform === 'cli')
    return `共有 ${cliScripts.length} 个 CLI 脚本。\n\n可以按类型筛选查看具体脚本。`
  }

  // 统计查询
  if (q.includes('多少') || q.includes('统计') || q.includes('总共')) {
    const byType: Record<string, number> = {}
    scripts.forEach(s => {
      byType[s.type] = (byType[s.type] || 0) + 1
    })
    const stats = Object.entries(byType)
      .sort((a, b) => b[1] - a[1])
      .map(([t, c]) => `• ${t}: ${c}个`)
      .join('\n')
    return `共有 ${scripts.length} 个脚本：\n\n${stats}`
  }

  // 如果有匹配的脚本
  if (matchedScripts.length > 0) {
    const list = matchedScripts.slice(0, 10).map(s => `• ${s.title}: ${s.description || s.name}`).join('\n')
    const more = matchedScripts.length > 10 ? `\n\n...还有 ${matchedScripts.length - 10} 个相关脚本` : ''
    return `找到 ${matchedScripts.length} 个相关脚本：\n\n${list}${more}`
  }

  // 默认回复
  return `我可以帮你查找脚本。试试问：
• 有哪些 Word 处理脚本？
• 有哪些格式转换脚本？
• 有多少个 Raycast 脚本？
• 有哪些 yabai 相关脚本？`
}
