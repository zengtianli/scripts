'use client'

import { useState, useMemo, useRef, useEffect } from 'react'
import scriptsData from '../data/scripts.json'

// 类型定义
interface Script {
  id: string
  name: string
  title: string
  description: string
  type: string
  function: string
  platform: string
  icon: string
  mode: string
  lines: number
  size: number
  path: string
  imports: string[]
  localImports: string[]
  externalImports: string[]
  linkedBy: string[]
  tags: string[]
}

interface TypeInfo {
  icon: string
  color: string
  name: string
}

interface Stats {
  total: number
  by_type: Record<string, number>
  by_function: Record<string, number>
  by_platform: Record<string, number>
}

// 平台颜色
const platformColors: Record<string, string> = {
  'raycast': 'bg-purple-100 text-purple-800',
  'cli': 'bg-gray-100 text-gray-800',
}

// 功能颜色
const functionColors: Record<string, string> = {
  'convert': 'bg-blue-100 text-blue-800',
  'format': 'bg-violet-100 text-violet-800',
  'analyze': 'bg-green-100 text-green-800',
  'automation': 'bg-amber-100 text-amber-800',
  'other': 'bg-gray-100 text-gray-600',
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function Home() {
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterFunction, setFilterFunction] = useState('')
  const [filterPlatform, setFilterPlatform] = useState('')
  const [selectedScript, setSelectedScript] = useState<Script | null>(null)

  // 聊天状态
  const [chatOpen, setChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<{role: 'user' | 'assistant', content: string}[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const data = scriptsData as {
    stats: Stats
    types: Record<string, TypeInfo>
    functions: Record<string, TypeInfo>
    scripts: Script[]
    generated_at: string
  }

  // 过滤脚本
  const filteredScripts = useMemo(() => {
    return data.scripts.filter(s => {
      // 搜索
      if (search) {
        const q = search.toLowerCase()
        const matchName = s.name.toLowerCase().includes(q)
        const matchTitle = s.title.toLowerCase().includes(q)
        const matchDesc = s.description.toLowerCase().includes(q)
        const matchTags = s.tags.some(t => t.toLowerCase().includes(q))
        if (!matchName && !matchTitle && !matchDesc && !matchTags) return false
      }
      // 类型过滤
      if (filterType && s.type !== filterType) return false
      // 功能过滤
      if (filterFunction && s.function !== filterFunction) return false
      // 平台过滤
      if (filterPlatform && s.platform !== filterPlatform) return false
      return true
    })
  }, [data.scripts, search, filterType, filterFunction, filterPlatform])

  // 按类型分组
  const groupedByType = useMemo(() => {
    const groups: Record<string, Script[]> = {}
    filteredScripts.forEach(s => {
      if (!groups[s.type]) groups[s.type] = []
      groups[s.type].push(s)
    })
    return groups
  }, [filteredScripts])

  // 打开脚本文件
  const openScript = async (path: string) => {
    try {
      await fetch('/api/open-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
    } catch {}
  }

  // 打开脚本所在目录
  const openFolder = async (path: string) => {
    try {
      await fetch('/api/open-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filePath: path }),
      })
    } catch {}
  }

  // 运行脚本
  const runScript = async (path: string) => {
    try {
      const res = await fetch('/api/run-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
      const result = await res.json()
      alert(result.success ? `✅ ${result.output || '执行成功'}` : `❌ ${result.error}`)
    } catch (e: any) {
      alert(`❌ 执行失败: ${e.message}`)
    }
  }

  // 发送聊天消息
  const sendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return

    const userMessage = chatInput.trim()
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setChatLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          scripts: data.scripts,
        }),
      })
      const result = await res.json()
      setChatMessages(prev => [...prev, { role: 'assistant', content: result.reply || '抱歉，我无法回答这个问题。' }])
    } catch (e: any) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: `❌ 错误: ${e.message}` }])
    } finally {
      setChatLoading(false)
    }
  }

  // 滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <header className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🛠️ 开发部脚本看板
          </h1>
          <p className="text-gray-500">
            共 {data.stats.total} 个脚本 · Raycast {data.stats.by_platform.raycast || 0} 个 · CLI {data.stats.by_platform.cli || 0} 个 · 更新于 {new Date(data.generated_at).toLocaleString('zh-CN')}
          </p>
        </div>
      </header>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {Object.entries(data.stats.by_type)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 8)
          .map(([type, count]) => {
            const info = data.types[type] || { icon: '📜', color: '#6B7280', name: type }
            return (
              <div
                key={type}
                className={`rounded-lg p-4 cursor-pointer transition hover:shadow-md border-l-4 bg-white ${
                  filterType === type ? 'ring-2 ring-blue-500' : ''
                }`}
                style={{ borderLeftColor: info.color }}
                onClick={() => setFilterType(filterType === type ? '' : type)}
              >
                <div className="text-2xl font-bold">{count}</div>
                <div className="text-sm text-gray-600">{info.icon} {info.name}</div>
              </div>
            )
          })}
      </div>

      {/* 搜索和过滤 */}
      <div className="flex flex-wrap gap-4 mb-6">
        <input
          type="text"
          placeholder="搜索脚本..."
          className="flex-1 min-w-[200px] px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={filterFunction}
          onChange={e => setFilterFunction(e.target.value)}
        >
          <option value="">全部功能</option>
          {Object.entries(data.functions).map(([name, info]) => (
            <option key={name} value={name}>
              {info.icon} {info.name}
            </option>
          ))}
        </select>
        <select
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={filterPlatform}
          onChange={e => setFilterPlatform(e.target.value)}
        >
          <option value="">全部平台</option>
          <option value="raycast">🚀 Raycast</option>
          <option value="cli">💻 CLI</option>
        </select>
        {(search || filterType || filterFunction || filterPlatform) && (
          <button
            className="px-4 py-2 text-gray-600 hover:text-gray-900"
            onClick={() => {
              setSearch('')
              setFilterType('')
              setFilterFunction('')
              setFilterPlatform('')
            }}
          >
            清除筛选
          </button>
        )}
      </div>

      {/* 脚本列表 - 按类型分组 */}
      <div className="space-y-8">
        {Object.entries(groupedByType)
          .sort((a, b) => b[1].length - a[1].length)
          .map(([type, scripts]) => {
            const info = data.types[type] || { icon: '📜', color: '#6B7280', name: type }
            return (
              <div key={type}>
                <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <span style={{ color: info.color }}>{info.icon}</span>
                  {info.name}
                  <span className="text-sm font-normal text-gray-400">({scripts.length})</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {scripts.map(script => (
                    <div
                      key={script.id}
                      className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition cursor-pointer"
                      onClick={() => setSelectedScript(script)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-lg">{script.icon}</span>
                        <div className="flex gap-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${functionColors[script.function] || functionColors.other}`}>
                            {data.functions[script.function]?.name || script.function}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${platformColors[script.platform]}`}>
                            {script.platform}
                          </span>
                        </div>
                      </div>
                      <h3 className="font-medium text-gray-900 mb-1">{script.title}</h3>
                      <p className="text-sm text-gray-500 line-clamp-2">{script.description || script.name}</p>
                      <div className="mt-2 text-xs text-gray-400">
                        {script.lines} 行 · {formatSize(script.size)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
      </div>

      {filteredScripts.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          没有找到匹配的脚本
        </div>
      )}

      {/* AI 聊天按钮 */}
      <button
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition flex items-center justify-center text-2xl z-40"
        onClick={() => setChatOpen(!chatOpen)}
      >
        {chatOpen ? '×' : '💬'}
      </button>

      {/* AI 聊天窗口 */}
      {chatOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-xl shadow-2xl border flex flex-col z-40">
          <div className="px-4 py-3 bg-blue-600 text-white rounded-t-xl flex items-center justify-between">
            <span className="font-medium">AI 助手</span>
            <button
              className="text-xs opacity-80 hover:opacity-100"
              onClick={() => setChatMessages([])}
            >
              清空
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {chatMessages.length === 0 && (
              <div className="text-center text-gray-400 py-8">
                <p>问我关于脚本的任何问题</p>
                <p className="text-sm mt-2">例如：有哪些 Word 处理脚本？</p>
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-3 py-2 rounded-lg text-sm text-gray-500">
                  思考中...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="p-3 border-t">
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="输入问题..."
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendMessage()
                  }
                }}
                disabled={chatLoading}
              />
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                onClick={sendMessage}
                disabled={chatLoading || !chatInput.trim()}
              >
                发送
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 脚本详情侧边栏 */}
      {selectedScript && (
        <div className="fixed inset-0 bg-black/50 z-50" onClick={() => setSelectedScript(null)}>
          <div
            className="absolute right-0 top-0 bottom-0 w-full max-w-lg bg-white shadow-xl overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            {/* 顶部导航 */}
            <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between z-10">
              <button
                className="flex items-center gap-1 text-gray-600 hover:text-gray-900"
                onClick={() => setSelectedScript(null)}
              >
                <span>←</span>
                <span>关闭</span>
              </button>
              <div className="flex gap-2">
                <button
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  onClick={() => openScript(selectedScript.path)}
                >
                  编辑
                </button>
                <button
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                  onClick={() => openFolder(selectedScript.path)}
                >
                  打开目录
                </button>
                {selectedScript.platform === 'cli' && (
                  <button
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                    onClick={() => runScript(selectedScript.path)}
                  >
                    运行
                  </button>
                )}
              </div>
            </div>

            <div className="p-6 space-y-4">
              {/* 标题 */}
              <div>
                <div className="text-4xl mb-2">{selectedScript.icon}</div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {selectedScript.title}
                </h2>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`px-3 py-1 rounded-full text-sm ${platformColors[selectedScript.platform]}`}>
                    {selectedScript.platform === 'raycast' ? '🚀 Raycast' : '💻 CLI'}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm ${functionColors[selectedScript.function] || functionColors.other}`}>
                    {data.functions[selectedScript.function]?.icon} {data.functions[selectedScript.function]?.name || selectedScript.function}
                  </span>
                </div>
              </div>

              {/* 描述 */}
              {selectedScript.description && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">描述</h4>
                  <p className="text-gray-700">{selectedScript.description}</p>
                </div>
              )}

              {/* 信息 */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">文件名</span>
                  <span className="font-mono text-sm">{selectedScript.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">类型</span>
                  <span>{data.types[selectedScript.type]?.name || selectedScript.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">代码行数</span>
                  <span>{selectedScript.lines} 行</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">文件大小</span>
                  <span>{formatSize(selectedScript.size)}</span>
                </div>
                {selectedScript.mode && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Raycast 模式</span>
                    <span>{selectedScript.mode}</span>
                  </div>
                )}
              </div>

              {/* 依赖 */}
              {selectedScript.externalImports && selectedScript.externalImports.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2">依赖模块</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedScript.externalImports.map(imp => (
                      <span
                        key={imp}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm font-mono"
                      >
                        {imp}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 双链 - Link Out */}
              {selectedScript.localImports && selectedScript.localImports.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
                    <span className="text-blue-500">→</span> Link Out
                    <span className="text-xs text-gray-400">依赖的本地脚本</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedScript.localImports.map(imp => {
                      const linkedScript = data.scripts.find(s => s.name.startsWith(imp))
                      return (
                        <span
                          key={imp}
                          className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm cursor-pointer hover:bg-blue-100"
                          onClick={() => linkedScript && setSelectedScript(linkedScript)}
                        >
                          {imp}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* 双链 - Link In */}
              {selectedScript.linkedBy && selectedScript.linkedBy.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-2 flex items-center gap-2">
                    <span className="text-green-500">←</span> Link In
                    <span className="text-xs text-gray-400">被 {selectedScript.linkedBy.length} 个脚本依赖</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedScript.linkedBy.map(scriptId => {
                      const linkedScript = data.scripts.find(s => s.id === scriptId)
                      return (
                        <span
                          key={scriptId}
                          className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-sm cursor-pointer hover:bg-green-100"
                          onClick={() => linkedScript && setSelectedScript(linkedScript)}
                        >
                          {linkedScript?.title || scriptId}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* 标签 */}
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">标签</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedScript.tags.map(tag => (
                    <span
                      key={tag}
                      className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm cursor-pointer hover:bg-blue-100"
                      onClick={() => {
                        setSelectedScript(null)
                        setSearch(tag)
                      }}
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* 路径 */}
              <div className="p-3 bg-gray-100 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">文件路径</p>
                <code className="text-xs text-gray-700 break-all">{selectedScript.path}</code>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
