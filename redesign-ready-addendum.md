# Addendum: Redesign-Ready Architecture untuk Mini App

## Tujuan

Memastikan Mini App Isha bisa di-redesign dengan mudah di masa depan tanpa rewrite business logic. Target: redesign total < 1 hari kerja.

## 3 Prinsip Redesign-Ready

### 1. Theme System via CSS Variables

**Semua nilai visual ada di satu file, pakai CSS variables.**

```css
/* webapp/assets/theme.css */
:root {
  /* === COLORS === */
  /* Primary palette */
  --color-primary: #378ADD;
  --color-primary-dark: #185FA5;
  --color-primary-light: #B5D4F4;
  
  /* Semantic */
  --color-success: #1D9E75;
  --color-warning: #EF9F27;
  --color-danger: #E24B4A;
  
  /* Surfaces */
  --color-bg: #FFFFFF;
  --color-bg-secondary: #F9F9F7;
  --color-bg-tertiary: #F1EFE8;
  
  /* Text */
  --color-text: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-tertiary: #9CA3AF;
  
  /* Borders */
  --color-border: #E5E7EB;
  --color-border-strong: #D1D5DB;
  
  /* === TYPOGRAPHY === */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'SF Mono', Consolas, monospace;
  
  --text-xs: 11px;
  --text-sm: 13px;
  --text-base: 15px;
  --text-lg: 18px;
  --text-xl: 22px;
  --text-2xl: 28px;
  
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  
  /* === SPACING === */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  
  /* === RADIUS === */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* === SHADOWS === */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  
  /* === TRANSITIONS === */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
}

/* Dark mode — auto from Telegram */
[data-theme="dark"] {
  --color-bg: #1F2937;
  --color-bg-secondary: #111827;
  --color-bg-tertiary: #0F172A;
  --color-text: #F9FAFB;
  --color-text-secondary: #D1D5DB;
  --color-text-tertiary: #9CA3AF;
  --color-border: #374151;
  --color-border-strong: #4B5563;
}
```

**Keuntungan:**
- Redesign = edit file `theme.css` saja
- Kalau mau bikin tema baru (misal "Dark Premium"), cukup tambah block `[data-theme="premium"]`
- Semua component otomatis ikut theme

### 2. Component Library

**Reusable component yang dipakai di semua halaman.**

```
webapp/assets/components/
├── Button.js              # Primary, secondary, danger button
├── Card.js                # Base card container
├── BudgetCard.js          # Specific budget card
├── ExpenseItem.js         # Expense list item
├── ProgressBar.js         # Progress bar dengan color
├── Modal.js               # Generic modal
├── FormField.js           # Input + label + error
├── Dropdown.js            # Select dropdown
├── Tabs.js                # Tab navigation
├── EmptyState.js          # Empty state illustration
├── LoadingSpinner.js      # Loading indicator
└── Toast.js               # Notification toast
```

**Contoh component:**

```javascript
// webapp/assets/components/Button.js
export function Button({ 
  label, 
  variant = 'primary',  // primary, secondary, danger, ghost
  size = 'md',          // sm, md, lg
  fullWidth = false,
  icon = null,
  onClick 
}) {
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth ? 'btn-full' : '',
  ].filter(Boolean).join(' ');
  
  return `
    <button class="${classes}" onclick="${onClick}">
      ${icon ? `<span class="btn-icon">${icon}</span>` : ''}
      <span>${label}</span>
    </button>
  `;
}
```

```css
/* webapp/assets/components/button.css */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-sans);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  cursor: pointer;
  transition: var(--transition-fast);
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-dark);
}

.btn-md { padding: var(--space-3) var(--space-4); font-size: var(--text-base); }
.btn-sm { padding: var(--space-2) var(--space-3); font-size: var(--text-sm); }
.btn-full { width: 100%; }
```

**Redesign Button di masa depan = edit `button.css` saja, semua tombol di app ikut berubah.**

### 3. Page Composition dengan Components

**Halaman = susunan components, bukan HTML custom per halaman.**

```javascript
// webapp/assets/pages/dashboard.js
import { Card } from '../components/Card.js';
import { BudgetCard } from '../components/BudgetCard.js';
import { ProgressBar } from '../components/ProgressBar.js';

export function renderDashboard(data) {
  return `
    <div class="page dashboard-page">
      ${Card({
        title: 'Total Terpakai',
        content: `
          <div class="stat-big">${formatIDR(data.totalSpent)}</div>
          <div class="stat-label">dari ${formatIDR(data.totalBudget)}</div>
          ${ProgressBar({ percentage: data.percentage, variant: 'primary' })}
        `
      })}
      
      <h2 class="section-title">Budget per Grup</h2>
      
      ${data.budgets.map(budget => BudgetCard({
        name: budget.name,
        spent: budget.spent,
        total: budget.amount,
        percentage: budget.percentage,
        status: budget.status,
      })).join('')}
    </div>
  `;
}
```

**Redesign dashboard = ubah order component atau ganti component, logic tetap sama.**

---

## Theme Variants (Future Ready)

Struktur memungkinkan multiple themes dengan mudah:

```css
/* webapp/assets/themes/minimalis.css — default */
[data-theme="minimalis"] { /* current style */ }

/* webapp/assets/themes/colorful.css */
[data-theme="colorful"] {
  --color-primary: #8B5CF6;
  --color-bg: #FEF3C7;
  --radius-md: 16px;  /* More rounded */
}

/* webapp/assets/themes/compact.css */
[data-theme="compact"] {
  --text-base: 13px;
  --space-4: 12px;
  /* Lebih padat */
}
```

User bisa pilih theme via setting:

```javascript
// Set theme
document.documentElement.setAttribute('data-theme', 'colorful');
localStorage.setItem('isha-theme', 'colorful');

// Load saved theme
const savedTheme = localStorage.getItem('isha-theme') || 'minimalis';
document.documentElement.setAttribute('data-theme', savedTheme);
```

---

## Redesign Workflow di Masa Depan

Kapan saja kamu mau redesign, ikuti langkah ini:

### Scenario 1: Tweak kecil (warna, spacing, radius)
**Effort: 30 menit**
1. Edit `webapp/assets/theme.css`
2. Ubah CSS variables yang mau di-tweak
3. Refresh Mini App di Telegram
4. Done — semua component ikut berubah

### Scenario 2: Redesign satu component (misal Button)
**Effort: 1 jam**
1. Edit `webapp/assets/components/button.css`
2. Test di semua halaman (karena Button dipakai di banyak tempat)
3. Commit & push
4. Done

### Scenario 3: Redesign satu halaman (misal Dashboard)
**Effort: 2-3 jam**
1. Edit `webapp/assets/pages/dashboard.js`
2. Susun ulang component, atau ganti component yang dipakai
3. Test flow
4. Done — logic & API tidak perlu disentuh

### Scenario 4: Redesign total (theme baru)
**Effort: 1 hari**
1. Buat `webapp/assets/themes/new-theme.css` dengan CSS variables baru
2. Kalau perlu component baru, tambah di `components/`
3. Update halaman yang mau pakai component baru
4. Test semua flow
5. Deploy

### Scenario 5: Migrasi ke framework (Vue/React)
**Effort: 2-3 hari**
Meskipun mulai dengan vanilla JS, arsitektur component + API yang terpisah bikin migrasi ke framework jauh lebih mudah. Component function tinggal dikonversi ke Vue/React component, API client tinggal di-import.

---

## Update ke File Structure

Tambahkan ke spec existing (`feature-telegram-miniapp.md`) struktur baru ini:

```
webapp/
├── index.html                     # Entry (minimal shell)
├── pages/
│   ├── dashboard.html             # Template shell (kosong, di-fill oleh JS)
│   ├── add-expense.html
│   ├── history.html
│   ├── budgets.html
│   └── reports.html
├── assets/
│   ├── theme.css                  # ⭐ Design tokens (EDIT untuk redesign)
│   ├── components/                # ⭐ Reusable components
│   │   ├── button.css + .js
│   │   ├── card.css + .js
│   │   ├── budget-card.css + .js
│   │   ├── expense-item.css + .js
│   │   ├── progress-bar.css + .js
│   │   ├── modal.css + .js
│   │   ├── form-field.css + .js
│   │   └── ...
│   ├── pages/                     # Page render functions
│   │   ├── dashboard.js
│   │   ├── add-expense.js
│   │   ├── history.js
│   │   ├── budgets.js
│   │   └── reports.js
│   ├── core/                      # Infrastructure
│   │   ├── api.js                 # API client
│   │   ├── router.js              # SPA router
│   │   ├── state.js               # State management
│   │   └── telegram.js            # Telegram WebApp wrapper
│   └── utils/
│       ├── formatters.js          # format_idr, format_date
│       └── validators.js
```

---

## Tasks Tambahan

Tambahkan ke Phase 2 (UI Shell) di spec Mini App:

- [ ] **T-806a**: Buat `webapp/assets/theme.css` dengan semua design tokens
- [ ] **T-806b**: Dark mode detection dari Telegram
- [ ] **T-812a**: Buat component: Button
- [ ] **T-812b**: Buat component: Card
- [ ] **T-812c**: Buat component: ProgressBar
- [ ] **T-812d**: Buat component: Modal
- [ ] **T-812e**: Buat component: FormField
- [ ] **T-812f**: Buat component: BudgetCard (specific)
- [ ] **T-812g**: Buat component: ExpenseItem (specific)

Update Phase 3-7:
- Setiap page render function pakai components yang sudah dibuat
- Tidak boleh ada inline style hardcoded di page
- Semua warna via CSS variable

---

## Aturan untuk Claude Code / Kiro

Saat implement Mini App, **WAJIB** ikuti:

1. **NEVER hardcode colors** — selalu `var(--color-xxx)`
2. **NEVER hardcode spacing** — selalu `var(--space-xxx)`
3. **NEVER hardcode font sizes** — selalu `var(--text-xxx)`
4. **Use components** — jangan bikin HTML custom kalau sudah ada component
5. **Create reusable** — kalau ada UI pattern dipakai 2x+, buat component
6. **Separate concerns** — HTML structure, CSS styling, JS logic, API data — semua terpisah
7. **Document CSS variables** — setiap variable baru di theme.css harus ada komentar singkat

**Di awal setiap page file, include import components:**

```javascript
// webapp/assets/pages/dashboard.js
import { Card } from '../components/card.js';
import { BudgetCard } from '../components/budget-card.js';
import { ProgressBar } from '../components/progress-bar.js';
import { formatIDR, formatDate } from '../utils/formatters.js';
```

---

## Kesimpulan

Dengan arsitektur ini:

✅ **Redesign kecil** (warna, spacing) = edit 1 file, 30 menit  
✅ **Redesign component** = edit 1-2 file, 1 jam  
✅ **Redesign halaman** = edit 1 file, 2-3 jam  
✅ **Redesign total** = 1 hari  
✅ **Multi-theme** = tambah file CSS variables baru  
✅ **Migrasi framework** = component function mudah dikonversi  

Semua tanpa sentuh business logic, API, atau database.

---

## Cara Pakai di Kiro

Kasih prompt ini saat mulai implement Mini App:

```
Aku mau implement Mini App dengan arsitektur redesign-ready.

Spec utama: .kiro/specs/miniapp/feature.md
Addendum redesign: .kiro/specs/miniapp/redesign-ready.md
Code standards: .kiro/steering/code-standards.md

Prinsip WAJIB:
1. Semua design tokens di theme.css (CSS variables)
2. Reusable components di components/
3. Page render function pakai components
4. No hardcoded values di HTML/JS
5. HTML structure, CSS styling, JS logic, API data TERPISAH

Mulai dari Phase 2 (UI Shell):
- Buat theme.css dengan semua design tokens
- Buat core components (Button, Card, ProgressBar, Modal, FormField)
- Setup router dan API client
- Bottom tab navigation

Baru lanjut ke Phase 3 (Dashboard) yang PAKAI components yang sudah dibuat.
```
