export async function api(path, options={}) {
  const response = await fetch('/api'+path, {credentials:'include', ...options, headers:{'Content-Type':'application/json','X-Requested-With':'pharmacy',...options.headers}});
  const data = await response.json().catch(()=>({detail:'Máy chủ không phản hồi đúng. Kiểm tra cửa sổ backend.'}));
  if (!response.ok) {
    if(response.status === 401 && path !== '/auth/login') window.dispatchEvent(new Event('session-expired'));
    const message = Array.isArray(data.detail) ? data.detail.map(x=>`${x.loc.slice(1).join('.')}: ${x.msg}`).join('; ') : data.detail;
    const error = new Error(message || 'Không thể thực hiện thao tác.');
    error.status = response.status;
    throw error;
  }
  return data;
}
export const send = (path, method, value) => api(path,{method,body:JSON.stringify(value)});
export const money = value => new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(Number(value || 0));
export const date = value => value ? new Date(value.length === 10 ? value+'T12:00:00' : value).toLocaleDateString('vi-VN') : '—';
export const localToday = () => new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
