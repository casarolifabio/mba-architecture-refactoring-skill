/**
 * Smoke tests reproduzíveis — ecommerce-api-legacy.
 * Sobe o servidor em porta efêmera, executa os 8 checks e encerra.
 * Uso: node scripts/smoke_test.js
 */
const http = require('http');
const { spawn } = require('child_process');
const path = require('path');
const net = require('net');

const ROOT = path.join(__dirname, '..');

function getFreePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, '127.0.0.1', () => {
      const { port } = s.address();
      s.close(() => resolve(port));
    });
    s.on('error', reject);
  });
}

function request(base, method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const u = new URL(base + urlPath);
    const req = http.request(
      {
        hostname: u.hostname,
        port: u.port,
        path: u.pathname,
        method,
        headers: data
          ? {
              'Content-Type': 'application/json',
              'Content-Length': Buffer.byteLength(data),
            }
          : {},
      },
      (res) => {
        let raw = '';
        res.on('data', (c) => (raw += c));
        res.on('end', () => {
          let json = null;
          try {
            json = JSON.parse(raw);
          } catch {
            /* text */
          }
          resolve({ status: res.statusCode, raw, json });
        });
      }
    );
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function waitReady(base, attempts = 40) {
  for (let i = 0; i < attempts; i++) {
    try {
      await request(base, 'GET', '/api/admin/financial-report');
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 100));
    }
  }
  throw new Error('Server did not become ready');
}

(async () => {
  const port = await getFreePort();
  const base = `http://127.0.0.1:${port}`;
  const child = spawn(process.execPath, ['src/app.js'], {
    cwd: ROOT,
    env: {
      ...process.env,
      PORT: String(port),
      PAYMENT_GATEWAY_KEY: 'dev-payment-key',
      DB_PATH: ':memory:',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let passed = 0;
  let failed = 0;
  const lines = [];
  const check = (name, cond, detail = '') => {
    if (cond) {
      passed += 1;
      lines.push(`PASS ${name}`);
    } else {
      failed += 1;
      lines.push(`FAIL ${name} ${detail}`);
    }
  };

  try {
    await waitReady(base);

    const ok = await request(base, 'POST', '/api/checkout', {
      usr: 'Guilherme',
      eml: 'gui-smoke@fullcycle.com.br',
      pwd: 'senhaforte',
      c_id: 2,
      card: '4111222233334444',
    });
    check(
      'checkout success 200 json',
      ok.status === 200 && ok.json && ok.json.msg === 'Sucesso' && ok.json.enrollment_id,
      JSON.stringify(ok)
    );

    const denied = await request(base, 'POST', '/api/checkout', {
      usr: 'Joao',
      eml: 'joao-smoke@teste.com',
      pwd: '123',
      c_id: 1,
      card: '5111222233334444',
    });
    check(
      'checkout denied 400',
      denied.status === 400 &&
        denied.json &&
        denied.json.error === 'Pagamento recusado',
      JSON.stringify(denied)
    );

    const bad = await request(base, 'POST', '/api/checkout', { usr: 'x' });
    check(
      'checkout bad request 400',
      bad.status === 400 && bad.json && bad.json.error === 'Bad Request',
      JSON.stringify(bad)
    );

    const nf = await request(base, 'POST', '/api/checkout', {
      usr: 'A',
      eml: 'a-smoke@b.com',
      pwd: 'x',
      c_id: 999,
      card: '4111',
    });
    check(
      'checkout course 404',
      nf.status === 404 && nf.json && nf.json.error === 'Curso não encontrado',
      JSON.stringify(nf)
    );

    const report = await request(base, 'GET', '/api/admin/financial-report');
    check(
      'financial report 200 array',
      report.status === 200 && Array.isArray(report.json) && report.json.length >= 1,
      JSON.stringify(report)
    );

    const docker = (report.json || []).find((c) => c.course === 'Docker');
    check(
      'financial report includes Docker after checkout',
      docker &&
        docker.revenue === 497 &&
        docker.students.some((s) => s.student === 'Guilherme'),
      JSON.stringify(docker)
    );

    const del = await request(base, 'DELETE', '/api/users/1');
    check(
      'delete user 200 text',
      del.status === 200 && String(del.raw).includes('Usuário deletado'),
      JSON.stringify(del)
    );

    const report2 = await request(base, 'GET', '/api/admin/financial-report');
    check(
      'financial report after delete',
      report2.status === 200 && Array.isArray(report2.json),
      JSON.stringify(report2)
    );
  } finally {
    child.kill('SIGTERM');
    await new Promise((r) => setTimeout(r, 200));
    try {
      child.kill('SIGKILL');
    } catch {
      /* ignore */
    }
  }

  console.log('==== SMOKE ecommerce-api-legacy ====');
  for (const l of lines) console.log(l);
  console.log(`PASSED=${passed} FAILED=${failed} TOTAL=${passed + failed}`);
  process.exit(failed ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
