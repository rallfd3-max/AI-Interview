/**
 * 超级助手 · 云端 mock 服务器
 *
 * 行为契约(与 protocol-contract.md 一致):
 *   收到 face   -> 落盘图片,回 person_info(canned 张三)
 *   收到 audio  -> 落盘音频,50% 概率回 hint
 *   收到 event(person_left) -> 回 clear
 *   收到 ping   -> 回 pong
 *
 * 数据落盘: mock/captures/  (face_*.jpg / audio_*.wav)
 * 启动:    cd mock && npm install && npm start
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const WebSocket = require('ws');

function lanCandidates() {
  const out = [];
  for (const [name, addrs] of Object.entries(os.networkInterfaces())) {
    const virtual = /WSL|Hyper-V|VMware|VirtualBox|Radmin|Loopback|蓝牙|Bluetooth|vEthernet|本地连接/i.test(name);
    for (const a of addrs || []) {
      if (a.family !== 'IPv4' || a.internal) continue;
      out.push({ name, ip: a.address, virtual });
    }
  }
  out.sort((x, y) => score(y) - score(x));
  return out;
}

function score(c) {
  let s = 0;
  if (/^192\.168\.|^10\./.test(c.ip)) s += 2;
  if (!c.virtual) s += 1;
  return s;
}

const PORT = process.env.PORT || 9000;
const CAPTURES_DIR = path.join(__dirname, 'captures');

if (!fs.existsSync(CAPTURES_DIR)) fs.mkdirSync(CAPTURES_DIR, { recursive: true });

function ts() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false });
}

function log(...args) {
  console.log(`[${ts()}]`, ...args);
}

const CANNED_PERSON = {
  type: 'person_info',
  id: 'p001',
  name: '张三',
  role: '前公司CTO',
  relation: '5年老朋友',
  last_met: '2026-03-15',
  notes: '对技术细节敏感',
  display_lines: [
    '张三',
    '前公司CTO / 5年老朋友',
    '上次见面:2026-03-15',
    '注意:对技术细节敏感',
  ],
  ts: 0,
};

const CANNED_HINTS = [
  '他上周提到项目延期',
  '可聊聊他儿子的升学',
  '上次约定一起看展',
  '他偏好直接的技术讨论',
];

function saveCapture(kind, ext, data) {
  const name = `${kind}_${Date.now()}_${crypto.randomBytes(2).toString('hex')}.${ext}`;
  fs.writeFileSync(path.join(CAPTURES_DIR, name), data);
  return name;
}

const wss = new WebSocket.Server({ port: PORT }, () => {
  log(`mock 服务器已启动, 端口 ${PORT}`);
  log(`采集文件目录: ${CAPTURES_DIR}`);
  const cands = lanCandidates();
  if (cands.length === 0) {
    log('警告: 未检测到可用局域网 IP, 手机无法连接');
    return;
  }
  log('手机端 App 服务器地址填写以下之一:');
  for (const c of cands) {
    const mark = score(c) === 3 ? ' <-- 推荐' : (c.virtual ? '  [虚拟网卡,勿用]' : '');
    log(`  ws://${c.ip}:${PORT}/ws  (${c.name})${mark}`);
  }
});

wss.on('connection', (ws, req) => {
  const deviceId = req.headers['x-device-id'] || 'unknown';
  log(`设备接入: ${deviceId} (${req.socket.remoteAddress})`);

  ws.on('message', (raw) => {
    let msg;
    try {
      msg = JSON.parse(raw.toString());
    } catch (e) {
      log('无法解析消息:', raw.toString().slice(0, 100));
      return;
    }

    switch (msg.type) {
      case 'ping':
        ws.send(JSON.stringify({ type: 'pong' }));
        return;

      case 'recognize':
      case 'face': {
        const buf = Buffer.from(msg.image_base64 || msg.img || '', 'base64');
        if (buf.length === 0) {
          log('收到 face 消息但图片为空');
          return;
        }
        const file = saveCapture('face', 'jpg', buf);
        log(`收到人脸图片 ${buf.length} 字节 (face_count=${msg.face_count ?? '-'} face_box=${JSON.stringify(msg.face_box) || '-'}) -> ${file}`);
        const person = { ...CANNED_PERSON, ts: Date.now() };
        setTimeout(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(person));
            log('已回 person_info: 张三');
          }
        }, 300);
        return;
      }

      case 'audio': {
        const buf = Buffer.from(msg.data || '', 'base64');
        if (buf.length === 0) {
          log('收到 audio 消息但数据为空');
          return;
        }
        const file = saveCapture('audio', 'wav', buf);
        log(`收到音频 ${buf.length} 字节 (duration_ms=${msg.duration_ms}) -> ${file}`);
        if (Math.random() < 0.5) {
          const text = CANNED_HINTS[Math.floor(Math.random() * CANNED_HINTS.length)];
          setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: 'hint',
                text,
                priority: 'high',
                topic: 'mock_' + Date.now(),
                display_ms: 5000,
                ts: Date.now(),
              }));
              log(`已回 hint: ${text}`);
            }
          }, 500);
        } else {
          log('本次静默,不推送 hint');
        }
        return;
      }

      case 'person_left':
      case 'event': {
        log(`收到事件: ${msg.event}`);
        if (msg.type === 'person_left' || msg.event === 'person_left') {
          ws.send(JSON.stringify({ type: 'clear', reason: 'person_left', ts: Date.now() }));
          log('已回 clear');
        }
        return;
      }

      default:
        log('未知消息类型:', msg.type);
    }
  });

  ws.on('close', () => log(`设备断开: ${deviceId}`));
  ws.on('error', (e) => log(`连接错误: ${e.message}`));
});
