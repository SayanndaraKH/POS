import os

STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(STATIC_IMG_DIR, exist_ok=True)

svg_templates = {
    'shop_logo.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="logoBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981" />
      <stop offset="100%" stop-color="#047857" />
    </linearGradient>
    <linearGradient id="cupGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#fef3c7" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="40" fill="url(#logoBg)"/>
  <!-- Boba Cup -->
  <path d="M60 65 L70 145 Q72 155 85 155 L115 155 Q128 155 130 145 L140 65 Z" fill="url(#cupGrad)" opacity="0.95"/>
  <!-- Tea Liquid -->
  <path d="M65 95 L72 143 Q73 150 85 150 L115 150 Q127 150 128 143 L135 95 Q100 102 65 95 Z" fill="#b45309" opacity="0.85"/>
  <!-- Boba Pearls -->
  <circle cx="85" cy="138" r="6" fill="#1c1917" />
  <circle cx="100" cy="140" r="7" fill="#1c1917" />
  <circle cx="115" cy="136" r="6.5" fill="#1c1917" />
  <circle cx="92" cy="126" r="6" fill="#292524" />
  <circle cx="108" cy="125" r="5.5" fill="#292524" />
  <!-- Straw -->
  <rect x="95" y="30" width="10" height="70" rx="5" transform="rotate(15 100 65)" fill="#f59e0b" stroke="#ffffff" stroke-width="2"/>
  <!-- Sparkles -->
  <path d="M150 45 L153 55 L163 58 L153 61 L150 71 L147 61 L137 58 L147 55 Z" fill="#fde047" />
  <circle cx="50" cy="55" r="4" fill="#a7f3d0" />
</svg>''',

    'brown_sugar_boba.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fffbeb"/>
      <stop offset="100%" stop-color="#fef3c7"/>
    </linearGradient>
    <linearGradient id="milk" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#fde68a"/>
    </linearGradient>
    <linearGradient id="sugarStreak" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#78350f"/>
      <stop offset="100%" stop-color="#451a03"/>
    </linearGradient>
  </defs>
  <rect width="240" height="240" rx="24" fill="url(#bg)"/>
  <!-- Straw -->
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#d97706" stroke="#fff" stroke-width="2"/>
  <!-- Cup Body -->
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="url(#milk)" stroke="#f59e0b" stroke-width="3"/>
  <!-- Brown Sugar dripping effects -->
  <path d="M72 120 Q85 140 90 190 L150 190 Q155 130 168 110 Q145 135 120 120 Q95 145 72 120 Z" fill="url(#sugarStreak)" opacity="0.9"/>
  <!-- Boba Pearls -->
  <circle cx="95" cy="188" r="9" fill="#1c1917" stroke="#451a03" stroke-width="1.5"/>
  <circle cx="118" cy="190" r="10" fill="#1c1917" stroke="#451a03" stroke-width="1.5"/>
  <circle cx="142" cy="186" r="9.5" fill="#1c1917" stroke="#451a03" stroke-width="1.5"/>
  <circle cx="106" cy="172" r="8.5" fill="#292524"/>
  <circle cx="130" cy="170" r="9" fill="#292524"/>
  <!-- Cup Rim -->
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#ffffff" stroke="#f59e0b" stroke-width="3"/>
  <!-- Ice cubes -->
  <rect x="90" y="85" width="22" height="22" rx="4" fill="#ffffff" opacity="0.6" transform="rotate(15 100 95)"/>
  <rect x="125" y="90" width="20" height="20" rx="4" fill="#ffffff" opacity="0.6" transform="rotate(-10 135 100)"/>
</svg>''',

    'matcha_latte.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%" height="100%">
  <defs>
    <linearGradient id="matchaBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ecfdf5"/>
      <stop offset="100%" stop-color="#d1fae5"/>
    </linearGradient>
    <linearGradient id="matchaGreen" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#047857"/>
    </linearGradient>
  </defs>
  <rect width="240" height="240" rx="24" fill="url(#matchaBg)"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#10b981" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#ffffff" stroke="#10b981" stroke-width="3"/>
  <!-- Matcha Layer -->
  <path d="M68 115 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L172 115 Q145 130 120 115 Q95 130 68 115 Z" fill="url(#matchaGreen)"/>
  <!-- Milk foam top -->
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#f0fdf4" stroke="#10b981" stroke-width="3"/>
  <!-- Matcha powder sprinkle -->
  <circle cx="105" cy="75" r="2" fill="#047857"/>
  <circle cx="120" cy="73" r="2.5" fill="#047857"/>
  <circle cx="135" cy="76" r="2" fill="#047857"/>
</svg>''',

    'classic_milk_tea.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%" height="100%">
  <defs>
    <linearGradient id="classicBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fff7ed"/>
      <stop offset="100%" stop-color="#ffedd5"/>
    </linearGradient>
    <linearGradient id="classicTea" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#d97706"/>
      <stop offset="100%" stop-color="#92400e"/>
    </linearGradient>
  </defs>
  <rect width="240" height="240" rx="24" fill="url(#classicBg)"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#78350f" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="url(#classicTea)" stroke="#d97706" stroke-width="3"/>
  <!-- Pearls -->
  <circle cx="95" cy="188" r="9" fill="#1c1917"/>
  <circle cx="118" cy="190" r="10" fill="#1c1917"/>
  <circle cx="142" cy="186" r="9.5" fill="#1c1917"/>
  <circle cx="106" cy="172" r="8.5" fill="#292524"/>
  <circle cx="130" cy="170" r="9" fill="#292524"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#fef3c7" stroke="#d97706" stroke-width="3"/>
</svg>''',

    'thai_tea.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%" height="100%">
  <rect width="240" height="240" rx="24" fill="#fff7ed"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#ea580c" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#ea580c" stroke="#c2410c" stroke-width="3"/>
  <!-- Milk swirl on top -->
  <path d="M68 95 Q90 120 120 100 Q150 120 172 95 L175 75 L65 75 Z" fill="#ffffff" opacity="0.85"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#ffffff" stroke="#ea580c" stroke-width="3"/>
</svg>''',

    'taro_milk_tea.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#faf5ff"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#9333ea" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#a855f7" stroke="#7e22ce" stroke-width="3"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#f3e8ff" stroke="#9333ea" stroke-width="3"/>
  <!-- Pearls -->
  <circle cx="95" cy="188" r="9" fill="#1c1917"/>
  <circle cx="118" cy="190" r="10" fill="#1c1917"/>
  <circle cx="142" cy="186" r="9.5" fill="#1c1917"/>
</svg>''',

    'iced_coffee.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fefce8"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#78350f" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#451a03" stroke="#78350f" stroke-width="3"/>
  <path d="M74 150 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L166 150 Z" fill="#fef3c7"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#78350f" stroke="#451a03" stroke-width="3"/>
</svg>''',

    'americano.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#f8fafc"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#0f172a" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#1c1917" stroke="#44403c" stroke-width="3"/>
  <!-- Ice cubes -->
  <rect x="85" y="90" width="25" height="25" rx="5" fill="#ffffff" opacity="0.4" transform="rotate(20 100 100)"/>
  <rect x="125" y="95" width="22" height="22" rx="5" fill="#ffffff" opacity="0.4" transform="rotate(-15 135 105)"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#292524" stroke="#44403c" stroke-width="3"/>
</svg>''',

    'latte.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fffbeb"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#b45309" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#d97706" stroke="#b45309" stroke-width="3"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#ffffff" stroke="#b45309" stroke-width="3"/>
</svg>''',

    'mocha.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fafaf9"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#713f12" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#3f2305" stroke="#713f12" stroke-width="3"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#fef3c7" stroke="#713f12" stroke-width="3"/>
</svg>''',

    'passion_tea.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fefce8"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#eab308" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#eab308" stroke="#ca8a04" stroke-width="3"/>
  <!-- Passion fruit seeds -->
  <circle cx="95" cy="130" r="3.5" fill="#1c1917"/>
  <circle cx="110" cy="150" r="4" fill="#1c1917"/>
  <circle cx="135" cy="140" r="3.5" fill="#1c1917"/>
  <circle cx="125" cy="175" r="4" fill="#1c1917"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#fef08a" stroke="#ca8a04" stroke-width="3"/>
</svg>''',

    'strawberry_smoothie.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fff1f2"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#f43f5e" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#fb7185" stroke="#e11d48" stroke-width="3"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#ffe4e6" stroke="#e11d48" stroke-width="3"/>
</svg>''',

    'lemon_tea.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fefce8"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#65a30d" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#84cc16" stroke="#65a30d" stroke-width="3"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#fef9c3" stroke="#65a30d" stroke-width="3"/>
</svg>''',

    'chocolate.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#fafaf9"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#451a03" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#451a03" stroke="#292524" stroke-width="3"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#78350f" stroke="#292524" stroke-width="3"/>
</svg>''',

    'matcha_cheese.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%">
  <rect width="240" height="240" rx="24" fill="#ecfdf5"/>
  <rect x="110" y="25" width="14" height="90" rx="7" transform="rotate(12 120 70)" fill="#10b981" stroke="#fff" stroke-width="2"/>
  <path d="M65 75 L78 190 Q80 205 100 205 L140 205 Q160 205 162 190 L175 75 Z" fill="#059669" stroke="#047857" stroke-width="3"/>
  <!-- Cheese foam layer -->
  <path d="M65 75 L68 115 Q120 120 172 115 L175 75 Z" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.5"/>
  <ellipse cx="120" cy="75" rx="55" ry="10" fill="#fffbeb" stroke="#f59e0b" stroke-width="3"/>
</svg>'''
}

for name, content in svg_templates.items():
    filepath = os.path.join(STATIC_IMG_DIR, name)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip())

print(f"Generated {len(svg_templates)} SVG assets in {STATIC_IMG_DIR}")
