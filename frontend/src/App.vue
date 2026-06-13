<template>
  <div class="app-container">
    <el-header class="header">
      <h1>
        <el-icon><Service /></el-icon>
        400热线工单管理系统
      </h1>
      <span class="subtitle">肯德基 · 麦当劳 · 华莱士 投诉管理</span>
    </el-header>
    <el-main class="main">
      <TicketList />
    </el-main>
  </div>
</template>

<script setup>
import TicketList from './components/TicketList.vue'
import { Service } from '@element-plus/icons-vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
}

.app-container {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 40px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.subtitle {
  opacity: 0.9;
  font-size: 14px;
}

.main {
  padding: 20px 40px;
}
</style>
