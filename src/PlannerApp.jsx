import { useEffect, useState } from 'react'
import Dashboard from './Dashboard'
import { api, clearToken, getStoredToken, storeToken } from './services/api'
import './PlannerApp.css'
import './AuthEntry.css'
import './PlanDetails.css'

const allergyOptions = ['dairy', 'nuts', 'gluten', 'sesame', 'soy', 'fish', 'egg']

function AuthScreen({ onSubmit, busy, error }) {
  const [mode, setMode] = useState(() => ['/signup', '/register'].includes(window.location.pathname) ? 'register' : 'login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const registering = mode === 'register'

  useEffect(() => {
    const syncRoute = () => setMode(['/signup', '/register'].includes(window.location.pathname) ? 'register' : 'login')
    window.addEventListener('popstate', syncRoute)
    return () => window.removeEventListener('popstate', syncRoute)
  }, [])

  function navigateAuth(nextMode) {
    const nextPath = nextMode === 'register' ? '/signup' : '/login'
    window.history.pushState({}, '', nextPath)
    setMode(nextMode)
  }

  function submit(event) {
    event.preventDefault()
    onSubmit({ ...(registering ? { name } : {}), email, password }, mode)
  }

  return (
    <main className="auth-screen">
      <section className="auth-story"><a className="brand" href="/"><span className="brand-mark">g</span><span>goodplate<span className="brand-period">.</span></span></a><div className="auth-story-copy"><span className="eyebrow"><i /> A MORE THOUGHTFUL TABLE</span><h1>Make room for<br />a little more <em>good.</em></h1><p>Personal meal ideas, a calmer plan, and a private place to keep it all together.</p><div className="auth-food-art" aria-hidden="true"><span>✳</span><i /><b /></div><div className="auth-story-actions"><button onClick={() => navigateAuth('register')}>Create your account <span>→</span></button><button onClick={() => navigateAuth('login')}>Already have an account? Sign in</button></div></div><div className="auth-footnote">A PERSONAL WELLNESS PLANNER · GENERAL EXAMPLES ONLY</div></section>
      <section className="auth-form-side"><div className="auth-form-wrap"><div className="auth-kicker">YOUR PERSONAL WORKSPACE</div><h2>{registering ? 'Create your account' : 'Welcome back'}</h2><p className="auth-lede">{registering ? 'A few details to get your workspace started.' : 'Sign in to pick up where you left off.'}</p><div className="auth-tabs" role="tablist"><button className={!registering ? 'selected' : ''} onClick={() => navigateAuth('login')} role="tab" aria-selected={!registering}>Sign in</button><button className={registering ? 'selected' : ''} onClick={() => navigateAuth('register')} role="tab" aria-selected={registering}>Create account</button></div><form onSubmit={submit} className="auth-form">{registering && <label>Your name<input autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} maxLength="80" required /></label>}<label>Email address<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" autoComplete={registering ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} minLength={registering ? 10 : 1} required /><small>{registering ? 'At least 10 characters' : 'Your account password'}</small></label>{error && <div className="inline-error" role="alert">{error}</div>}<button className="button-primary auth-submit" disabled={busy}>{busy ? 'Please wait…' : registering ? 'Create account' : 'Sign in'} <span>→</span></button></form><div className="auth-privacy"><span>◈</span><p>Your demo profile and plans are private to your account. Use synthetic data for coursework demos.</p></div><p className="auth-disclaimer">General wellness examples only. Not medical advice.</p></div></section>
    </main>
  )
}

function ProfileEditor({ profile, userName, onSave, busy, notice }) {
  const [form, setForm] = useState({
    name: profile?.name || userName || '', age: profile?.age ?? '', height_cm: profile?.height_cm ?? '', weight_kg: profile?.weight_kg ?? '',
    activity_level: profile?.activity_level || 'light', dietary_preference: profile?.dietary_preference || 'omnivore',
    goal: profile?.goal || 'balanced', allergies: profile?.allergies || [], preferences: profile?.preferences || '',
  })
  function change(event) { setForm((previous) => ({ ...previous, [event.target.name]: event.target.value })) }
  function toggleAllergy(item) { setForm((previous) => ({ ...previous, allergies: previous.allergies.includes(item) ? previous.allergies.filter((value) => value !== item) : [...previous.allergies, item] })) }
  function submit(event) {
    event.preventDefault()
    onSave({ ...form, age: form.age ? Number(form.age) : null, height_cm: form.height_cm ? Number(form.height_cm) : null, weight_kg: form.weight_kg ? Number(form.weight_kg) : null })
  }
  return <form className="profile-form surface" onSubmit={submit}><div className="form-grid"><label>Name<input name="name" value={form.name} onChange={change} required maxLength="80" /></label><label>Age <span>optional demo field</span><input type="number" name="age" min="18" max="100" value={form.age} onChange={change} /></label><label>Height (cm) <span>optional</span><input type="number" name="height_cm" min="120" max="230" value={form.height_cm} onChange={change} /></label><label>Weight (kg) <span>optional</span><input type="number" name="weight_kg" min="35" max="300" value={form.weight_kg} onChange={change} /></label><label>Activity level<select name="activity_level" value={form.activity_level} onChange={change}><option value="low">Mostly seated</option><option value="light">Light movement</option><option value="moderate">Moderately active</option><option value="high">Very active</option></select></label><label>Dietary preference<select name="dietary_preference" value={form.dietary_preference} onChange={change}><option value="omnivore">General / omnivore</option><option value="vegetarian">Vegetarian</option><option value="vegan">Vegan</option></select></label><label className="wide-field">General wellness goal<select name="goal" value={form.goal} onChange={change}><option value="balanced">Balanced eating</option><option value="weight-management">Weight-management demo</option><option value="fitness">Fitness-oriented demo</option></select></label><fieldset className="wide-field"><legend>Allergies to exclude from suggestions</legend><div className="allergy-list">{allergyOptions.map((item) => <label key={item}><input type="checkbox" checked={form.allergies.includes(item)} onChange={() => toggleAllergy(item)} />{item}</label>)}</div></fieldset><label className="wide-field">Foods or cuisines you enjoy <span>optional</span><textarea name="preferences" value={form.preferences} onChange={change} maxLength="300" rows="3" placeholder="e.g. quick lunches, Mediterranean flavors" /></label></div><div className="form-foot"><p>{notice || 'Your profile is used only to shape general meal suggestions.'}</p><button className="button-primary" disabled={busy}>{busy ? 'Saving…' : 'Save profile'} <span>→</span></button></div></form>
}

function PageHeading({ eyebrow, title, children }) { return <div className="route-heading"><div><span className="section-index">{eyebrow}</span><h1>{title}</h1></div>{children}</div> }

function MealPlan({ plan, onExport }) {
  if (!plan) return <div className="empty-state surface"><span>✳</span><h2>Your next good thing starts here.</h2><p>Save your profile preferences, then create a flexible, general-wellness meal example.</p></div>
  return <div className="plan-result">
    <div className="plan-disclaimer">{plan.disclaimer}</div>
    <div className="plan-meals">{['breakfast', 'lunch', 'snack', 'dinner'].map((key, index) => <article className="plan-meal surface" key={key}><div><span className="section-index">0{index + 1} / {key.toUpperCase()}</span><h2>{plan[key]?.name}</h2><p>{plan[key]?.description}</p></div><span className="plan-calories">~{plan[key]?.calories} kcal</span></article>)}</div>
    <section className="nutrition-summary surface">
      <div><span className="section-index">APPROXIMATE DAILY SUMMARY</span><h2>{plan.nutrition_summary?.approximate_calories ?? '—'} <small>kcal</small></h2><p>{plan.nutrition_summary?.note}</p>
        {plan.nutrition_summary?.approximate_macros_g && <ul className="macro-list">{Object.entries(plan.nutrition_summary.approximate_macros_g).map(([name, amount]) => <li key={name}><span>{name}</span><strong>~{amount} g</strong></li>)}</ul>}
      </div>
      <div className="water-note"><span>◌</span><div><strong>A gentle reminder</strong><p>{plan.hydration_reminder}</p></div></div>
    </section>
    <div className="plan-actions"><span>Generated with {plan.generation_mode === 'optional-ai' ? 'optional AI assistance' : 'the local rules engine'}</span><button className="button-secondary" onClick={onExport}>↓ Export plan</button></div>
  </div>
}

export default function PlannerApp() {
  const [token, setToken] = useState(getStoredToken)
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [plans, setPlans] = useState([])
  const [files, setFiles] = useState([])
  const [activeView, setActiveView] = useState('Overview')
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(Boolean(token))
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    if (!token) return undefined
    let active = true
    Promise.all([api.profile(), api.plans(), api.files()]).then(([nextProfile, nextPlans, nextFiles]) => {
      if (!active) return
      setProfile(nextProfile.profile)
      setUser({ name: nextProfile.name, email: nextProfile.email })
      setPlans(nextPlans)
      setFiles(nextFiles)
      setLoading(false)
    }).catch((reason) => {
      if (!active) return
      if (reason.message === 'Sign in to continue') { clearToken(); setToken(null) }
      setError(reason.message)
      setLoading(false)
    })
    return () => { active = false }
  }, [token])

  async function authenticate(values, mode) {
    setBusy(true); setLoading(true); setError('')
    try {
      const result = mode === 'register' ? await api.register(values) : await api.login(values)
      storeToken(result.access_token)
      window.history.replaceState({}, '', '/')
      setUser(result.user)
      setToken(result.access_token)
      setActiveView(mode === 'register' ? 'Profile' : 'Overview')
    } catch (reason) { setError(reason.message) }
    finally { setBusy(false) }
  }

  async function saveProfile(values) {
    setBusy(true); setError(''); setNotice('')
    try {
      const saved = await api.saveProfile(values)
      setProfile(saved.profile); setUser({ name: saved.name, email: saved.email }); setNotice('Profile saved. Your next plan will use these preferences.')
    } catch (reason) { setError(reason.message) }
    finally { setBusy(false) }
  }

  async function generatePlan() {
    setBusy(true); setError(''); setNotice('')
    try {
      const plan = await api.generatePlan()
      setPlans((current) => [plan, ...current]); setSelectedPlan(plan); setActiveView('Meal planner'); setNotice('Your plan has been saved to your private workspace.')
    } catch (reason) { setError(reason.message) }
    finally { setBusy(false) }
  }

  async function refreshFiles() { setFiles(await api.files()) }
  async function removeFile(id) {
    try { await api.deleteFile(id); await refreshFiles(); setNotice('Image removed from your private file library.') }
    catch (reason) { setError(reason.message) }
  }
  async function uploadFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setBusy(true); setError(''); setNotice('')
    try { await api.uploadFile(file); await refreshFiles(); setNotice('Image uploaded to your private file library.') }
    catch (reason) { setError(reason.message) }
    finally { setBusy(false); event.target.value = '' }
  }

  async function removePlan(id) {
    try { await api.deletePlan(id); setPlans((current) => current.filter((plan) => plan.id !== id)); if (selectedPlan?.id === id) setSelectedPlan(null); setNotice('Plan removed.') }
    catch (reason) { setError(reason.message) }
  }

  async function downloadFile(file) {
    try {
      const blob = await api.downloadFile(file.id)
      const url = URL.createObjectURL(blob); const anchor = document.createElement('a')
      anchor.href = url; anchor.download = file.filename; anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (reason) { setError(reason.message) }
  }

  function exportPlan(plan = selectedPlan || plans[0]) {
    if (!plan) return
    const blob = new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob); const anchor = document.createElement('a')
    anchor.href = url; anchor.download = `goodplate-plan-${plan.id.slice(0, 8)}.json`; anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  async function logout() {
    await api.logout().catch(() => {})
    window.history.replaceState({}, '', '/login')
    clearToken(); setToken(null); setUser(null); setProfile(null); setPlans([]); setFiles([]); setSelectedPlan(null); setActiveView('Overview'); setError(''); setLoading(false)
  }

  if (!token) return <AuthScreen onSubmit={authenticate} busy={busy} error={error} />
  if (loading) return <main className="loading-screen"><span className="loading-mark">g</span><p>Opening your workspace…</p></main>

  const latestPlan = plans[0]
  let pageContent
  if (activeView === 'Profile') pageContent = <><PageHeading eyebrow="03 / YOUR DETAILS" title="A plan that feels like you." /><p className="page-lede">These optional demo preferences guide general meal suggestions. They are not used for clinical calculations.</p><ProfileEditor key={profile?.name || user?.name || 'profile'} profile={profile} userName={user?.name} onSave={saveProfile} busy={busy} notice={notice} /></>
  if (activeView === 'Meal planner') pageContent = <><PageHeading eyebrow="04 / FLEXIBLE BY DESIGN" title="Your meal plan"><button className="button-primary" onClick={generatePlan} disabled={busy}>{busy ? 'Building…' : '＋ Generate a new plan'}</button></PageHeading><p className="page-lede">A starting point, not a prescription. Every plan is saved automatically to your account.</p>{notice && <p className="success-note" role="status">{notice}</p>}<MealPlan plan={selectedPlan || latestPlan} onExport={() => exportPlan(selectedPlan || latestPlan)} /></>
  if (activeView === 'My plans') pageContent = <><PageHeading eyebrow="05 / YOUR LIBRARY" title="Saved plans"><button className="button-primary" onClick={generatePlan} disabled={busy}>＋ New plan</button></PageHeading>{plans.length ? <div className="saved-plan-list">{plans.map((plan) => <article className="saved-plan-row surface" key={plan.id}><button className="saved-plan-open" onClick={() => { setSelectedPlan(plan); setActiveView('Meal planner') }}><span className="saved-plan-icon">▤</span><span><strong>{plan.breakfast?.name || 'Personal meal plan'}</strong><small>{new Date(plan.created_at).toLocaleString()} · {plan.generation_mode}</small></span><b>→</b></button><button className="delete-button" aria-label="Delete plan" onClick={() => removePlan(plan.id)}>×</button></article>)}</div> : <div className="empty-state surface"><h2>No saved plans yet</h2><p>Your generated plans will appear here.</p><button className="button-primary" onClick={generatePlan}>Build a meal plan <span>→</span></button></div>}</>
  if (activeView === 'Cloud files') pageContent = <><PageHeading eyebrow="06 / PRIVATE STORAGE" title="Your food library"><label className="button-primary upload-button">＋ Upload an image<input type="file" accept="image/jpeg,image/png,image/webp" onChange={uploadFile} disabled={busy} /></label></PageHeading><p className="page-lede">JPEG, PNG or WebP · 5 MB maximum. Files are private to your account.</p>{files.length ? <div className="file-list surface">{files.map((file) => <article className="file-row" key={file.id}><span className="file-icon">▧</span><div><strong>{file.filename}</strong><small>{(file.size_bytes / 1024).toFixed(0)} KB · {new Date(file.created_at).toLocaleDateString()}</small></div><button className="button-secondary" onClick={() => downloadFile(file)}>↓ Download</button><button className="delete-button" aria-label={`Delete ${file.filename}`} onClick={() => removeFile(file.id)}>×</button></article>)}</div> : <div className="empty-state surface"><span>▧</span><h2>A home for your food inspiration.</h2><p>Upload a demo meal image to try private file storage.</p></div>}</>
  if (activeView === 'Overview') return <Dashboard user={user} profile={profile} plans={plans} files={files} latestPlan={latestPlan} onGenerate={generatePlan} onNavigate={setActiveView} activeView={activeView} onLogout={logout}>
    {error && <div className="global-error" role="alert">{error}<button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
    {notice && <p className="success-note" role="status">{notice}</p>}
  </Dashboard>

  return <Dashboard user={user} profile={profile} plans={plans} files={files} latestPlan={latestPlan} onGenerate={generatePlan} onNavigate={setActiveView} activeView={activeView} onLogout={logout}>
    {error && <div className="global-error" role="alert">{error}<button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}
    {pageContent}
  </Dashboard>
}
