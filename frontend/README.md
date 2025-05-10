## 前端部署
进入前端目录
```bash
cd frontend
```

安装依赖
```bash
npm install
```

如果安装依赖报错
1. 检查node版本：
```bash
node --version
v22.12.0

```
2. 检查npm源
```bash
npm config set registry https://registry.npmmirror.com/
npm install
```

开发模式运行
```bash
npm run dev
```