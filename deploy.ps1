# Set UTF-8 encoding for full Khmer language support
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "POS Tea - One-Click GitHub & Vercel Deploy"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "   🚀 កម្មវិធីស្វ័យប្រវត្តិ៖ រុញកូដទៅ GitHub និង Deploy ទៅកាន់ Vercel" -ForegroundColor Green
Write-Host "   ☕ Boba POS System - Auto Deploy Tool" -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. ពិនិត្យមើល Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[កំហុស] រកមិនឃើញកម្មវិធី Git ក្នុងកុំព្យូទ័រនេះទេ!" -ForegroundColor Red
    Write-Host "សូមដំឡើង Git ជាមុនសិន: https://git-scm.com/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "ចុច Enter ដើម្បីចាកចេញ..."
    exit 1
}

# 2. ពិនិត្យមើល Git Repository
if (-not (Test-Path ".git")) {
    Write-Host "[*] កំពុងបង្កើត Git Repository ថ្មី..." -ForegroundColor Cyan
    git init -b main
    Write-Host ""
}

# 3. ពិនិត្យមើល Remote Origin
$remote = git remote get-url origin 2>$null
if (-not $remote) {
    Write-Host "[!] មិនទាន់មាន Link GitHub Repository នៅឡើយទេ។" -ForegroundColor Yellow
    $repoUrl = Read-Host "សូមបញ្ចូល Link GitHub Repo របស់អ្នក (ឧ. https://github.com/username/pos.git)"
    if ([string]::IsNullOrWhiteSpace($repoUrl)) {
        Write-Host "[កំហុស] អ្នកមិនបានបញ្ចូល Link GitHub ទេ!" -ForegroundColor Red
        Read-Host "ចុច Enter ដើម្បីចាកចេញ..."
        exit 1
    }
    git remote add origin $repoUrl
    Write-Host "[+] បានភ្ជាប់ទៅកាន់: $repoUrl" -ForegroundColor Green
    Write-Host ""
}

# 4. សួររក Commit Message
Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host "[*] កំពុងរៀបចំ File ទាំងអស់ដើម្បី Push..." -ForegroundColor Cyan
Write-Host ""
$userMsg = Read-Host "សូមវាយអត្ថន័យនៃការ Update (ឬចុច Enter ដើម្បីយកលំនាំដើម)"

if ([string]::IsNullOrWhiteSpace($userMsg)) {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $userMsg = "Update POS Tea - $now"
}

Write-Host ""
Write-Host "[*] កំពុង Add Files (git add .)..." -ForegroundColor Cyan
git add .

Write-Host "[*] កំពុងបង្កើត Commit: '$userMsg'..." -ForegroundColor Cyan
git commit -m "$userMsg"

Write-Host ""
Write-Host "[*] កំពុងរុញកូដឡើងទៅកាន់ GitHub (git push origin main)..." -ForegroundColor Cyan
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Green
    Write-Host "   🎉 ជោគជ័យ! (DEPLOYMENT SUCCESS)" -ForegroundColor Green
    Write-Host "   -------------------------------------------------------------------------" -ForegroundColor Gray
    Write-Host "   ✅ កូដត្រូវបាន Push ទៅកាន់ GitHub រួចរាល់ដោយជោគជ័យ!" -ForegroundColor White
    Write-Host "   🚀 Vercel នឹងចាប់ផ្ដើម Deploy ដោយស្វ័យប្រវត្តិក្នុងរយៈពេលប្រហែល ១ នាទី។" -ForegroundColor White
    Write-Host ""
    Write-Host "   🌐 ពិនិត្យមើលវេបសាយផ្ទាល់: https://pos-six-murex.vercel.app" -ForegroundColor Cyan
    Write-Host "   📊 ពិនិត្យមើល Vercel Dashboard: https://vercel.com/" -ForegroundColor Cyan
    Write-Host "===============================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "===============================================================================" -ForegroundColor Red
    Write-Host "   ⚠️ ការ Push មិនទាន់បានសម្រេច! (PUSH FAILED)" -ForegroundColor Red
    Write-Host "   -------------------------------------------------------------------------" -ForegroundColor Gray
    Write-Host "   សូមពិនិត្យមើល៖" -ForegroundColor Yellow
    Write-Host "   1. ត្រូវប្រាកដថាបាន Login GitHub ក្នុងម៉ាស៊ីនរួចហើយ" -ForegroundColor White
    Write-Host "   2. ពិនិត្យមើល Link GitHub Repository ថាត្រឹមត្រូវដែរឬទេ" -ForegroundColor White
    Write-Host "===============================================================================" -ForegroundColor Red
}

Write-Host ""
Read-Host "ចុច Enter ដើម្បីបិទផ្ទាំងនេះ..."
