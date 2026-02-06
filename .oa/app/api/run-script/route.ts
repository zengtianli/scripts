import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    const { path } = await request.json()

    if (!path) {
      return NextResponse.json({ error: '缺少脚本路径' }, { status: 400 })
    }

    // 判断脚本类型
    const isPython = path.endsWith('.py')
    const isShell = path.endsWith('.sh') || path.endsWith('.zsh')

    let command: string
    if (isPython) {
      command = `python3 "${path}"`
    } else if (isShell) {
      command = `bash "${path}"`
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
