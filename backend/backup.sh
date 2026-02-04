#!/bin/bash

# ChatBI 后端服务备份脚本
# 用于定期备份数据库和关键文件

# 配置
BACKUP_DIR="/backup/chatbi"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="chatbi"
DB_USER="root"
DB_PASSWORD="your_strong_password"

# 创建备份目录（如果不存在）
mkdir -p $BACKUP_DIR/database $BACKUP_DIR/config $BACKUP_DIR/uploads $BACKUP_DIR/logs

# 1. 数据库备份
echo "[$(date)] 开始数据库备份..."
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/database/chatbi_${DATE}.sql
if [ $? -eq 0 ]; then
    gzip $BACKUP_DIR/database/chatbi_${DATE}.sql
    echo "[$(date)] 数据库备份完成: chatbi_${DATE}.sql.gz"
else
    echo "[$(date)] 数据库备份失败!"
fi

# 2. 配置文件备份
echo "[$(date)] 开始配置文件备份..."
tar -czf $BACKUP_DIR/config/chatbi_config_${DATE}.tar.gz \
    /opt/chatbi/backend/.env \
    /opt/chatbi/backend/docker-compose.yml \
    /etc/nginx/sites-available/chatbi \
    /etc/systemd/system/chatbi-backend.service \
    /etc/logrotate.d/chatbi
if [ $? -eq 0 ]; then
    echo "[$(date)] 配置文件备份完成: chatbi_config_${DATE}.tar.gz"
else
    echo "[$(date)] 配置文件备份失败!"
fi

# 3. 上传文件备份
echo "[$(date)] 开始上传文件备份..."
tar -czf $BACKUP_DIR/uploads/chatbi_uploads_${DATE}.tar.gz /var/www/chatbi/uploads/
if [ $? -eq 0 ]; then
    echo "[$(date)] 上传文件备份完成: chatbi_uploads_${DATE}.tar.gz"
else
    echo "[$(date)] 上传文件备份失败!"
fi

# 4. 日志文件备份
echo "[$(date)] 开始日志文件备份..."
tar -czf $BACKUP_DIR/logs/chatbi_logs_${DATE}.tar.gz /var/log/chatbi/*.log /var/log/nginx/*.log
if [ $? -eq 0 ]; then
    echo "[$(date)] 日志文件备份完成: chatbi_logs_${DATE}.tar.gz"
else
    echo "[$(date)] 日志文件备份失败!"
fi

# 5. 清理旧备份（保留最近7天）
echo "[$(date)] 清理旧备份..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# 6. 记录备份日志
echo "[$(date)] 备份完成" >> $BACKUP_DIR/backup.log

# 7. 检查备份完整性
if [ -f "$BACKUP_DIR/database/chatbi_${DATE}.sql.gz" ] && \
   [ -f "$BACKUP_DIR/config/chatbi_config_${DATE}.tar.gz" ] && \
   [ -f "$BACKUP_DIR/uploads/chatbi_uploads_${DATE}.tar.gz" ]; then
    echo "[$(date)] 所有备份均成功完成"
else
    echo "[$(date)] 部分备份失败，请检查日志"
fi

# 8. 发送通知（可选）
# echo "ChatBI 备份完成" | mail -s "ChatBI 备份通知" admin@example.com

exit 0