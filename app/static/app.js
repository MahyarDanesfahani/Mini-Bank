const $ = (s) => document.querySelector(s);
const loginForm = $('#loginForm'), registerForm = $('#registerForm'), notice = $('#notice');
function setMode(mode) {
  const signup = mode === 'register';
  loginForm.hidden = signup; registerForm.hidden = !signup;
  $('#loginTab').classList.toggle('active', !signup); $('#registerTab').classList.toggle('active', signup);
  $('#modeLabel').textContent = signup ? 'عضویت در صندوق‌من' : 'خوش آمدید';
  $('#title').textContent = signup ? 'ساخت حساب کاربری' : 'ورود به حساب';
  $('#subtitle').textContent = signup ? 'برای عضویت، اطلاعات خود را وارد کنید.' : 'برای ادامه، وارد حساب کاربری‌تان شوید.';
  notice.hidden = true;
}
$('#loginTab').addEventListener('click', () => setMode('login'));
$('#registerTab').addEventListener('click', () => setMode('register'));
document.querySelectorAll('.peek').forEach(button => button.addEventListener('click', () => {
  const input = button.previousElementSibling; input.type = input.type === 'password' ? 'text' : 'password';
}));
$('#forgot').addEventListener('click', e => { e.preventDefault(); showNotice('برای بازیابی گذرواژه، با مدیر صندوق تماس بگیرید.', 'success'); });
function showNotice(message, kind = 'error') { notice.textContent = message; notice.className = `notice ${kind}`; notice.hidden = false; }
function faDigits(value) { return value.replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))); }
function jalaliToIso(jy, jm, jd) {
  jy += 1595;
  let days = -355668 + 365 * jy + Math.floor(jy / 33) * 8 + Math.floor(((jy % 33) + 3) / 4) + jd + (jm < 7 ? (jm - 1) * 31 : (jm - 7) * 30 + 186);
  let gy = 400 * Math.floor(days / 146097); days %= 146097;
  if (days > 36524) { gy += 100 * Math.floor(--days / 36524); days %= 36524; if (days >= 365) days++; }
  gy += 4 * Math.floor(days / 1461); days %= 1461;
  if (days > 365) { gy += Math.floor((days - 1) / 365); days = (days - 1) % 365; }
  let gd = days + 1;
  const leap = gy % 4 === 0 && (gy % 100 !== 0 || gy % 400 === 0);
  const months = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let gm = 0; while (gd > months[gm]) gd -= months[gm++];
  return `${gy}-${String(gm + 1).padStart(2, '0')}-${String(gd).padStart(2, '0')}`;
}
function detailMessage(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(x => x.msg).join('، ');
  return 'در انجام درخواست مشکلی پیش آمد.';
}
async function api(path, body) {
  const response = await fetch(`/api/v1/auth/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(detailMessage(data.detail));
  return data;
}
function busy(form, active) { const button = form.querySelector('.submit'); button.disabled = active; button.dataset.label ??= button.innerHTML; button.innerHTML = active ? 'لطفاً صبر کنید…' : button.dataset.label; }
loginForm.addEventListener('submit', async e => {
  e.preventDefault(); notice.hidden = true;
  if (!loginForm.reportValidity()) return;
  const body = Object.fromEntries(new FormData(loginForm)); body.national_code = faDigits(body.national_code); busy(loginForm, true);
  try { const data = await api('token', body); localStorage.setItem('mini_bank_token', data.access_token); location.href = '/dashboard'; }
  catch (error) { showNotice(error.message); } finally { busy(loginForm, false); }
});
registerForm.addEventListener('submit', async e => {
  e.preventDefault(); notice.hidden = true;
  if (!registerForm.reportValidity()) return;
  const body = Object.fromEntries(new FormData(registerForm));
  body.national_code = faDigits(body.national_code); body.postal_code = faDigits(body.postal_code);
  body.phone = faDigits(body.phone).replace(/[\s-]/g, '');
  body.birth_date = jalaliToIso(Number(faDigits(body.birth_year)), Number(body.birth_month), Number(faDigits(body.birth_day)));
  body.birth_year = body.birth_month = body.birth_day = undefined;
  if (body.email) body.email = body.email.trim(); else delete body.email;
  delete body.birth_year; delete body.birth_month; delete body.birth_day;
  busy(registerForm, true);
  try { await api('register', body); const token = await api('token', {national_code: body.national_code, password: body.password}); localStorage.setItem('mini_bank_token', token.access_token); location.href = '/dashboard'; }
  catch (error) { showNotice(error.message); } finally { busy(registerForm, false); }
});
