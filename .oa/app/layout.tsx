import './globals.css'

export const metadata = {
  title: '开发部脚本看板',
  description: 'useful_scripts 脚本管理系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
