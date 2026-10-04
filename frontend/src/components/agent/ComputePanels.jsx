import { useEffect, useState } from 'react';
import { Coins, Plus, Play, Settings2, Pause, ShieldCheck } from 'lucide-react';
import { Btn, Field, Modal } from '../Kit';
import { Switch } from '../ui/switch';
import { useWallet } from '../WalletContext';

export const CreditPanel = ({ data, busy, action, onEstimate }) => {
  const [limits, setLimits] = useState(false);
  const [perRun, setPerRun] = useState(20), [perDay, setPerDay] = useState(50);
  const { openWallet } = useWallet();
  const savedRunLimit = data?.per_run_limit, savedDailyLimit = data?.daily_limit;
  useEffect(() => { if (savedRunLimit != null) { setPerRun(savedRunLimit); setPerDay(savedDailyLimit); } }, [savedRunLimit, savedDailyLimit]);
  if (!data) return <aside className="compute-credit-panel" data-testid="compute-credit-loading">Menyiapkan kredit…</aside>;
  const running = !!data.active_run;
  return <aside className="compute-credit-panel" data-testid="hub-compute-credit-card">
    <div className="compute-panel-heading"><span><Coins size={15} />KREDIT COMPUTE</span><span className="compute-test-tag" data-testid="compute-test-mode">KREDIT UJI</span></div>
    <div className="compute-balance"><span data-testid="compute-balance-label">Saldo tersedia</span><strong data-testid="hub-compute-balance">{data.balance.toFixed(2)}<small>CR</small></strong><span className="compute-reserved" data-testid="compute-reserved">{data.reserved.toFixed(4)} CR direservasi</span></div>
    <div className="compute-mini-stats"><div><span>Terpakai</span><strong data-testid="compute-spent">{data.spent.toFixed(4)} CR</strong></div><div><span>Riset selesai</span><strong data-testid="compute-completed">{data.runs_completed.toString().padStart(2, '0')}</strong></div></div>
    <div className="compute-daily"><div><span>Pemakaian hari ini</span><strong data-testid="compute-daily-spend">{data.day_spent.toFixed(2)} / {data.daily_limit} CR</strong></div><div className="compute-progress"><span style={{ width: `${Math.min(100, data.day_spent / data.daily_limit * 100)}%` }} /></div><span data-testid="compute-run-limit">Maks. {data.per_run_limit} CR / riset · {data.remaining_daily_runs} riset tersisa hari ini</span></div>
    <button className="compute-estimate-link" data-testid="compute-before-topup-estimate" onClick={onEstimate}>Lihat estimasi sebelum isi kredit ↗</button>
    <Btn secondary busy={busy === 'topup'} disabled={!data.can_manage || !!busy} data-testid="hub-top-up-credits-button" onClick={() => action('topup', { amount: 100, request_id: crypto.randomUUID() })}><Plus size={15} />Isi 100 kredit uji</Btn>
    <Btn busy={running || busy === 'runs'} disabled={!data.can_manage || !data.runnable || data.paused || data.balance === 0 || !!busy || running || !data.remaining_daily_runs} data-testid="hub-manual-run-button" onClick={() => action('runs', { request_id: crypto.randomUUID() })}>{running ? <span>Riset sedang berjalan</span> : <><Play size={14} fill="currentColor" />Jalankan Agent</>}</Btn>
    <div className="compute-controls"><button data-testid="compute-limits-open" disabled={!data.can_manage || running} onClick={() => setLimits(true)}><Settings2 size={13} />Batas biaya</button><button data-testid="compute-pause" disabled={!data.can_manage || running || !!busy} onClick={() => action('limits', { per_run_limit: data.per_run_limit, daily_limit: data.daily_limit, paused: !data.paused }, 'PATCH')}><Pause size={13} />{data.paused ? 'Lanjutkan' : 'Jeda'}</button></div>
    {!data.can_manage && <button className="text-link" data-testid="compute-creator-connect" onClick={openWallet}>Hubungkan wallet kreator ↗</button>}
    {!data.runnable && <p className="compute-warning" data-testid="compute-provider-unavailable">Model belum terhubung atau research tidak diaktifkan kreator.</p>}
    <p className="compute-fineprint" data-testid="compute-credit-disclaimer"><ShieldCheck size={12} />Kredit internal, bukan uang atau aset. Riset memakai AI sungguhan. Tidak ada transaksi otomatis.</p>
    <Modal open={limits} onClose={() => setLimits(false)} id="compute-limits" title="Batas biaya agent" description="Reservasi harus muat dalam batas per riset dan sisa batas harian. Hari dihitung dalam UTC.">
      <form className="form-stack" data-testid="compute-limits-form" onSubmit={async e => { e.preventDefault(); if (await action('limits', { per_run_limit: Number(perRun), daily_limit: Number(perDay), paused: data.paused }, 'PATCH')) setLimits(false); }}>
        <Field id="compute-limit-per-run" label="Batas per riset (CR)" type="number" min="0.01" max="50" step="0.01" required value={perRun} onChange={e => setPerRun(e.target.value)} />
        <Field id="compute-limit-daily" label="Batas harian (CR)" type="number" min="0.01" max="200" step="0.01" required value={perDay} onChange={e => setPerDay(e.target.value)} />
        <Btn type="submit" busy={busy === 'limits'} data-testid="compute-limits-save">Simpan batas</Btn>
      </form>
    </Modal>
  </aside>;
};

export const SchedulePanel = ({ data, busy, action, frequency }) => <div className="compute-schedule" data-testid="compute-schedule-panel">
  <div><strong data-testid="compute-schedule-title">Riset terjadwal</strong><p data-testid="compute-schedule-status">{!data?.manual_completed ? 'Terkunci · selesaikan satu riset manual' : data.schedule.enabled ? 'Aktif · ' + data.schedule.frequency : 'Siap diaktifkan'}</p></div>
  <Switch aria-label="Aktifkan riset terjadwal" data-testid="hub-scheduled-work-toggle" checked={!!data?.schedule.enabled} disabled={!data?.manual_completed || !data?.can_manage || data?.paused || !!busy} onCheckedChange={enabled => action('schedule', { enabled, frequency }, 'PATCH')} />
  {data?.schedule.enabled && <p className="compute-schedule-next" data-testid="compute-next-run">Berikutnya: {new Date(data.schedule.next_run_at).toLocaleString('id-ID')} · pemeriksaan setiap 15 menit<br />Masa uji 7 hari; berhenti saat kredit atau batas habis.</p>}
  {data?.schedule.enabled && data.schedule.frequency !== frequency && data.can_manage && <button className="text-link" data-testid="compute-schedule-apply-frequency" disabled={!!busy} onClick={() => action('schedule', { enabled: true, frequency }, 'PATCH')}>Terapkan frekuensi baru ↗</button>}
</div>;