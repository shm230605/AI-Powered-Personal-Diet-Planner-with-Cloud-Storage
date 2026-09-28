import './Dashboard.css'

const meals = [
  { label: 'BREAKFAST', time: '8:30 AM', name: 'Honeyed pear oats', detail: 'Toasted hazelnut · warm cinnamon', tone: 'oat', icon: '◒' },
  { label: 'LUNCH', time: '12:45 PM', name: 'Green goddess bowl', detail: 'Crispy chickpea · herby tahini', tone: 'green', icon: '✳' },
  { label: 'DINNER', time: '7:00 PM', name: 'Miso-glazed salmon', detail: 'Sesame greens · brown rice', tone: 'rose', icon: '⌁' },
]

const navItems = ['Overview', 'Meal planner', 'My plans', 'Cloud files', 'Profile']
const today = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: '2-digit' }).toUpperCase()

export default function Dashboard({ user, profile, plans = [], files = [], latestPlan, onGenerate, onNavigate, activeView = 'Overview', onLogout, children }) {
  const displayedMeals = latestPlan ? meals.map((meal, index) => {
    const key = ['breakfast', 'lunch', 'dinner'][index]
    const item = latestPlan[key]
    return item ? { ...meal, name: item.name, detail: item.description, calories: item.calories } : meal
  }) : meals
  const goalLabels = { balanced: 'Balanced eating', 'weight-management': 'Weight-management demo', fitness: 'Fitness-oriented demo' }
  const preferenceLabels = { omnivore: 'General / omnivore', vegetarian: 'Vegetarian', vegan: 'Vegan' }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => onNavigate('Overview')}><span className="brand-mark">g</span><span>goodplate<span className="brand-period">.</span></span></button>
        <div className="workspace-label">YOUR WORKSPACE</div>
        <nav className="primary-nav" aria-label="Main navigation">
          {navItems.map((item, index) => <button className={`nav-item ${activeView === item ? 'active' : ''}`} key={item} onClick={() => onNavigate(item)}><span>{['◫', '⌘', '▤', '▧', '◉'][index]}</span>{item}{item === 'My plans' && plans.length > 0 && <small>{plans.length}</small>}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="storage-note"><span>☁</span><div><strong>{files.length} private files</strong><small>Personal workspace</small></div><i /></div>
          <div className="account"><span className="avatar">{(user?.name || 'U').split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}</span><div><strong>{user?.name || 'Your account'}</strong><small>{user?.email || 'Personal account'}</small></div><button className="account-more" onClick={onLogout} aria-label="Sign out">↗</button></div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><b>/</b><strong>{activeView}</strong></div><div className="top-actions"><span className="date-chip">{today}</span><button className="notification" aria-label="Notifications">♧<i /></button></div></header>
        <div className="page-content">{activeView === 'Overview' ? <>
          {children}
          <section className="welcome-row"><div><div className="eyebrow"><i /> YOUR WEEK, IN BALANCE</div><h1>A little more <em>good</em> in every day.</h1><p>A thoughtful plan makes room for the things you love.</p></div><button className="button-primary" onClick={onGenerate}><span>＋</span> Build a meal plan</button></section>
          <section className="hero-grid">
            <article className="feature-card"><div className="feature-top"><span className="pill"><i /> THIS WEEK</span><span>↗</span></div><div className="feature-copy"><small>A steadier rhythm</small><h2>Make space for<br />eating well.</h2><p>Small, satisfying choices add up. Your plan is a flexible starting point, made around you.</p><a href="#planner" onClick={(event) => { event.preventDefault(); onNavigate('Meal planner') }}>See your meal plan <b>→</b></a></div><div className="food-art" aria-hidden="true"><div className="plate"><span className="food-leaf leaf-a"/><span className="food-leaf leaf-b"/><span className="food-tomato tomato-a"/><span className="food-tomato tomato-b"/><span className="food-grain grain-a"/><span className="food-grain grain-b"/></div><span className="art-spark">✳</span><span className="art-caption">GOOD FOOD<br />GOOD MOOD</span></div></article>
            <article className="summary-card"><div className="card-title"><div><small>01 / YOUR SNAPSHOT</small><h2>Your focus</h2></div><button onClick={() => onNavigate('Profile')} aria-label="Edit profile">···</button></div><div className="focus-row"><span className="focus-symbol">✳</span><div><small>YOUR GOAL</small><strong>{goalLabels[profile?.goal] || 'Choose a wellness goal'}</strong></div><button onClick={() => onNavigate('Profile')} aria-label="Edit goal">↗</button></div><div className="focus-row"><span className="focus-symbol peach">◒</span><div><small>YOUR PREFERENCE</small><strong>{preferenceLabels[profile?.dietary_preference] || 'Choose a preference'}</strong></div><button onClick={() => onNavigate('Profile')} aria-label="Edit preference">↗</button></div><div className="progress-block"><div><small>SAVED PLANS</small><strong>{plans.length} <i>in your library</i></strong></div><div className="progress-track"><span style={{ width: `${Math.min(plans.length * 20, 100)}%` }} /></div><div className="week-days"><span>Plan</span><span>your</span><span>week</span><span>at</span><span>your</span><span>own</span><span>pace</span></div></div></article>
          </section>
          <section className="section-heading"><div><small>02 / YOUR TABLE</small><h2>On the menu today</h2></div><a href="#planner" onClick={(event) => { event.preventDefault(); onNavigate('Meal planner') }}>View full plan <b>→</b></a></section>
          <section className="meal-grid">{displayedMeals.map((meal) => <article className="meal-card" key={meal.label}><div className={`meal-art ${meal.tone}`}><span>{meal.icon}</span><small>{meal.calories || (meal.label === 'LUNCH' ? '520' : meal.label === 'DINNER' ? '610' : '380')} kcal</small></div><div className="meal-meta"><span>{meal.label}</span><time>{meal.time}</time></div><h3>{meal.name}</h3><p>{meal.detail}</p></article>)}</section>
          <section className="bottom-row"><article className="note-card"><span>✳</span><div><small>A SMALL REMINDER</small><h3>Progress, not perfection.</h3><p>Plans support you. Swap, skip, or savor whatever feels right today.</p></div><b>✳</b></article><article className="cloud-card"><div className="cloud-card-top"><small>YOUR LIBRARY</small><span>● SAVED</span></div><div className="saved-plan"><span>▤</span><div><h3>{plans[0]?.breakfast?.name || 'Your saved plans'}</h3><p>{plans.length} plan{plans.length === 1 ? '' : 's'} · {files.length} private file{files.length === 1 ? '' : 's'}</p></div><button onClick={() => onNavigate('My plans')} aria-label="Open saved plans">→</button></div><div className="cloud-card-footer"><span>STORED IN YOUR PRIVATE WORKSPACE</span><span>{String(plans.length).padStart(2, '0')} SAVED</span></div></article></section>
          <footer className="footer-note"><span>GOODPLATE · PERSONAL WELLNESS PLANNER</span><span>GENERAL WELLNESS EXAMPLE · NOT MEDICAL ADVICE</span></footer>
        </> : children}</div>
      </main>
    </div>
  )
}