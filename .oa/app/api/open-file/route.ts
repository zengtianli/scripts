import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const { path } = await request.json()

    if (!path) {
      return NextResponse.json({ error: '缺少文件路径' }, { status: 400 })
    }

    // 使用 VS Code 打开文件
    exec(`code "${path}"`, (error) => {
      if (error) {
        // 如果 VS Code 失败，尝试用默认编辑器
        exec(`open "${path}"`)
      }
    })

    return NextResponse.json({ success: true })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
