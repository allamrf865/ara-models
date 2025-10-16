# 🌸 Deploy ARA Radar v2.0 ke Orchids App

## ✅ Project Structure - Ready for Orchids!

Project ini sudah direstruktur agar kompatibel dengan Orchids App:

```
ara-models/
├── app/              ← Next.js App Router
├── components/       ← React components
├── lib/              ← Utilities
├── public/           ← Static assets
├── next.config.js    ← Next.js config ✓
├── package.json      ← Dependencies ✓
├── tsconfig.json     ← TypeScript config ✓
├── tailwind.config.js ← Tailwind config ✓
├── .env.local        ← Environment variables ✓
└── backend/          ← FastAPI backend (deploy terpisah)
```

## 🚀 Deploy Frontend ke Orchids App

### Step 1: Import dari GitHub

1. Buka Orchids App dashboard
2. Click "Import from GitHub"
3. Masukkan URL: `https://github.com/allamrf865/ara-models`
4. Orchids akan otomatis detect Next.js project ✓

### Step 2: Set Environment Variables

Di Orchids dashboard, tambahkan environment variables:

```env
NEXT_PUBLIC_BACKEND_URL=https://ara-radar-backend.fly.dev
NEXT_PUBLIC_SUPABASE_URL=https://wxddgrcnjesgumfztcdi.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind4ZGRncmNuamVzZ3VtZnp0Y2RpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1OTA1NTQsImV4cCI6MjA3NjE2NjU1NH0.VhrJ5h7RNZNyWQS3E1fa4Rn0rvs17XAlNGAugWly2o0
```

### Step 3: Configure Build Settings

Orchids akan auto-detect, tapi pastikan:

- **Framework**: Next.js 14
- **Build command**: `npm run build` (atau otomatis)
- **Output directory**: `.next` (atau otomatis)
- **Install command**: `npm install` (atau otomatis)

### Step 4: Deploy!

Click "Deploy" dan tunggu ~2-3 menit.

## 🔧 Deploy Backend ke Fly.io (Terpisah)

Backend tetap di-deploy ke Fly.io karena Orchids fokus pada frontend:

```bash
cd backend

# Login ke Fly.io
fly auth login

# Deploy
fly launch --name ara-radar-backend --region sin
fly secrets set \
  SUPABASE_URL=https://wxddgrcnjesgumfztcdi.supabase.co \
  SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind4ZGRncmNuamVzZ3VtZnp0Y2RpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1OTA1NTQsImV4cCI6MjA3NjE2NjU1NH0.VhrJ5h7RNZNyWQS3E1fa4Rn0rvs17XAlNGAugWly2o0

fly deploy
```

Setelah backend deploy, update `NEXT_PUBLIC_BACKEND_URL` di Orchids dengan URL backend Fly.io.

## 📋 Post-Deployment Checklist

Setelah deployment sukses di Orchids:

- [ ] Frontend accessible di URL Orchids
- [ ] Landing page load dengan aurora animation
- [ ] Dashboard tampil tanpa error
- [ ] Ingest wizard accessible
- [ ] API calls ke backend berhasil
- [ ] Supabase connection works

## ✨ Fitur yang Ready

### Frontend (Orchids App)
- ✅ Next.js 14 App Router
- ✅ Server-side rendering
- ✅ Static page generation
- ✅ API routes (proxy)
- ✅ Image optimization
- ✅ Automatic code splitting

### Backend (Fly.io)
- ✅ FastAPI dengan 20+ endpoints
- ✅ Multi-ingest (8 sumber)
- ✅ XGBoost scoring
- ✅ Real-time SSE alerts
- ✅ Supabase integration

### Database (Supabase)
- ✅ 3 tables dengan RLS
- ✅ Dataset storage
- ✅ Alert scheduling
- ✅ Trading calendar

## 🐛 Troubleshooting

### "This repository is not a Vite or Next.js project"

**Solved!** Files Next.js sudah di root level:
- ✅ next.config.js
- ✅ package.json
- ✅ app/ directory
- ✅ tsconfig.json

Refresh import atau push changes ke GitHub.

### Build Fails on Orchids

Check logs untuk error spesifik:
- Dependency conflicts → Sudah pakai `--legacy-peer-deps`
- TypeScript errors → Semua file sudah valid
- Environment variables → Set di Orchids dashboard

### CORS Errors

Backend sudah configured untuk CORS `*`, tapi jika masih error:
1. Verify `NEXT_PUBLIC_BACKEND_URL` correct
2. Check backend logs: `fly logs`
3. Test backend health: `curl https://ara-radar-backend.fly.dev/health`

### SSE Alerts Not Working

- Check browser console untuk connection errors
- Verify `/alerts/stream` endpoint accessible
- Try disabling adblockers yang bisa block SSE

## 💰 Cost Estimate

**Total: $0-5/month**

- **Orchids App**: Check pricing (biasanya free tier available)
- **Fly.io Backend**: $0 (free tier 256MB) atau $1.94/month
- **Supabase**: $0 (free tier 500MB)

## 📊 Expected Performance

### Frontend (Orchids)
- First load: ~1.5s
- Page transitions: <300ms
- Build time: ~30s
- Global CDN delivery

### Backend (Fly.io)
- API latency: <500ms
- Cold start: ~3s
- Scoring: <2s for k≤100

## 🎯 Verification Tests

### 1. Frontend Health
Visit Orchids URL → Should see landing page

### 2. API Connection
```bash
# Test dari browser console
fetch('https://your-orchids-url.app/api/proxy/health')
  .then(r => r.json())
  .then(console.log)
```

### 3. Full E2E Test
1. Go to `/ingest`
2. Upload CSV file
3. Check dashboard for results
4. Verify alerts work

## 📚 Architecture

```
┌─────────────────┐
│  Orchids App    │ ← Frontend (Next.js 14)
│  (CDN + SSR)    │
└────────┬────────┘
         │
         ├──────────► Backend (Fly.io)
         │            FastAPI + XGBoost
         │
         └──────────► Database (Supabase)
                      PostgreSQL
```

## 🚀 Quick Commands

```bash
# Clone repo
git clone https://github.com/allamrf865/ara-models.git

# Check structure
ls -la next.config.js package.json app/

# Deploy backend
cd backend && fly deploy

# Deploy frontend → Use Orchids UI
```

## 📖 Documentation Links

- **Next.js 14 Docs**: https://nextjs.org/docs
- **Orchids App Docs**: Check Orchids dashboard
- **Fly.io Docs**: https://fly.io/docs
- **Supabase Docs**: https://supabase.com/docs

## 🎉 Success Criteria

Deployment sukses jika:

✅ Orchids detect Next.js project
✅ Build completes tanpa error
✅ Frontend accessible via Orchids URL
✅ Backend API calls berhasil
✅ Database queries work
✅ All 8 pages load correctly
✅ Ingest wizard functional
✅ SSE alerts streaming

---

## 💡 Tips

1. **Push to GitHub first** sebelum import ke Orchids
2. **Set environment variables** sebelum deploy
3. **Deploy backend dulu** agar URL ready untuk frontend
4. **Test locally** dengan `npm run dev` sebelum push
5. **Monitor logs** di Orchids dan Fly.io dashboard

## 🆘 Need Help?

1. Check Orchids logs untuk error messages
2. Verify all environment variables set
3. Test backend independently: `fly logs`
4. Check Supabase dashboard untuk database issues
5. Review `DEPLOYMENT_GUIDE.md` untuk alternative methods

---

**Version**: 2.0.0
**Last Updated**: October 16, 2025
**Status**: ✅ Ready for Orchids App

🌸 **Happy Deploying dengan Orchids!**
