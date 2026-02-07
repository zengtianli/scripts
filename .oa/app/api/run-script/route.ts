import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    const { path: scriptPath, mode } = await request.json()

    if (!scriptPath) {
      return NextResponse.json({ error: '缺少脚本路径' }, { status: 400 })
    }

    let command: string
    const cwd = path.dirname(scriptPath)

    if (mode === 'streamlit') {
      // Streamlit 模式：在后台启动，打开浏览器
      command = `cd "${cwd}" && streamlit run "${path.basename(scriptPath)}" &`
      try {
        exec(command, { timeout: 5000 })
        // 等一秒让 streamlit 启动
        await new Promise(resolve => setTimeout(resolve, 1500))
        exec('open "http://localhost:8501"')
        return NextResponse.json({
          success: true,
          output: `Streamlit 应用已启动: ${path.basename(scriptPath)}`,
        })
      } catch (error: any) {
        return NextResponse.json({
          success: false,
          error: error.message || 'Streamlit 启动失败',
        }, { status: 500 })
      }
    }

    // 普通脚本模式
    const isPython = scriptPath.endsWith('.py')
    const isShell = scriptPath.endsWith('.sh') || scriptPath.endsWith('.zsh')

    if (isPython) {
      command = `python3 "${scriptPath}"`
    } else if (isShell) {
      command = `bash "${scriptPath}"`
    } else {
      return NextResponse.json({ error: '不支持的脚本类型' }, { status: 400 })
    }

    const { stdout, stderr } = await execAsync(command, {
      timeout: 30000, // 30秒超时
      maxBuffer: 1024 * 1024, // 1MB
    })

    return NextResponse.json({
      success: true,
      output: stdout || stderr || '执行完成',
    })
  } catch (error: any) {
    return NextResponse.json({
      success: false,
      error: error.message || '执行失败',
    }, { status: 500 })
  }
}
