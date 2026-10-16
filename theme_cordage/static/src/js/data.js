/* =============================================
   CORDAGE — Shared product & category data
   ============================================= */

/**
 * Shared category data for the Cordage theme demo mode.
 * Defines the industries/categories available for filtering.
 * @constant {Array<Object>}
 */
const CATEGORIES = [
  { id:'industrial', name:'Industrial',  icon:'⚙️',  tagline:'Heavy-duty cordage',   gradient:'linear-gradient(135deg,#3d2008,#8b5e1a)' },
  { id:'marine',     name:'Marine',      icon:'⚓',  tagline:'Salt & UV resistant',  gradient:'linear-gradient(135deg,#0d2340,#1e5080)' },
  { id:'fabric',     name:'Fabric',      icon:'🧵',  tagline:'Soft braided ropes',   gradient:'linear-gradient(135deg,#5a3a20,#b07840)' },
  { id:'climbing',   name:'Climbing',    icon:'🧗',  tagline:'Certified safety',     gradient:'linear-gradient(135deg,#5a0a0a,#c0392b)' },
];

/**
 * Shared product data for the Cordage theme demo mode.
 * Contains detailed specifications and properties for demo products.
 * @constant {Array<Object>}
 */
const PRODUCTS = [
  /* ——— Industrial ——— */
  {
    id:'p1', name:'Industrial Manila Rope', cat:'industrial',
    price:24.90, unit:'/ 10m', pricePerM:2.49, rating:4.8, reviews:312, badge:'Bestseller',
    ropeClass:'rt-manila', imgUrl:'/images/img3.jpg',
    shortDesc:'Coarse natural fibre rope for rigging, towing and heavy loads.',
    fullDesc:'Three-strand twisted Manila rope made from Agave sisalana fibres. Renowned for high grip, natural flexibility, and UV resistance. Ideal for rigging, towing, lashing, and decorative maritime applications. Sold per metre — cut to your exact length.',
    specs:{Diameter:'12 mm',Material:'Natural Manila Fibre',Construction:'3-strand twisted','WLL':'800 kg','Breaking Strength':'2,400 kg',Colour:'Natural tan-brown','UV Resistance':'Good'},
    tags:['12mm','Natural fibre','High grip'], related:['p2','p3']
  },
  {
    id:'p2', name:'Polypropylene Utility Rope', cat:'industrial',
    price:14.50, unit:'/ 15m', pricePerM:0.97, rating:4.6, reviews:188, badge:'',
    ropeClass:'rt-poly', imgUrl:'/images/img6.webp',
    shortDesc:'Lightweight, rot-proof rope for general site and warehouse use.',
    fullDesc:'High-tenacity polypropylene braided rope resistant to rot, mildew, and most chemicals. Lightweight and easy to handle — perfect for warehouse lashing, site safety cordons, and outdoor applications. Does not absorb water, making it ideal for damp environments.',
    specs:{Diameter:'10 mm',Material:'Polypropylene (PP)',Construction:'Braided','WLL':'560 kg','Breaking Strength':'1,680 kg',Colour:'Blue/Gold twist','UV Resistance':'Excellent'},
    tags:['10mm','Waterproof','Lightweight'], related:['p1','p3']
  },
  {
    id:'p3', name:'Steel-Core Hoist Rope', cat:'industrial',
    price:58.00, unit:'/ 10m', pricePerM:5.80, rating:4.9, reviews:97, badge:'Pro',
    ropeClass:'rt-steel', imgUrl:'/images/img1.jpg',
    shortDesc:'Galvanised steel core sheathed in fibre for maximum load safety.',
    fullDesc:'Industrial-grade rope with a galvanised steel wire core and synthetic fibre outer sheath. Provides the mechanical strength of steel wire with improved flexibility. Certified for hoists, cranes, and overhead lifting up to 2.5T WLL.',
    specs:{Diameter:'16 mm',Material:'Galvanised steel core + PP sheath',Construction:'Wire-core braid','WLL':'2,500 kg','Breaking Strength':'7,500 kg',Colour:'Silver-grey',Certifications:'EN 13414, CE marked'},
    tags:['16mm','Steel core','2.5T WLL'], related:['p1','p2']
  },
  /* ——— Marine ——— */
  {
    id:'p4', name:'Marine Double-Braid Rope', cat:'marine',
    price:39.90, unit:'/ 10m', pricePerM:3.99, rating:4.9, reviews:204, badge:'New',
    ropeClass:'rt-marine', imgUrl:'/images/img4.jpg',
    shortDesc:'Low-stretch braided rope for mooring, halyards and sheets.',
    fullDesc:'High-performance double-braid polyester rope for demanding marine environments. The inner core provides exceptional strength and low stretch, while the outer braid resists UV, abrasion, and saltwater. Ideal for mooring, halyards, sheets, and all running rigging.',
    specs:{Diameter:'12 mm',Material:'Polyester (core + braid)',Construction:'Double braid','WLL':'1,200 kg','Breaking Strength':'3,600 kg',Colour:'Navy Blue/White','UV Resistance':'Excellent','Elongation at WLL':'< 2%'},
    tags:['12mm','UV stable','Low stretch'], related:['p5','p6']
  },
  {
    id:'p5', name:'Anchor Nylon Rope', cat:'marine',
    price:32.00, unit:'/ 20m', pricePerM:1.60, rating:4.7, reviews:156, badge:'',
    ropeClass:'rt-nylon', imgUrl:'/images/img5.webp',
    shortDesc:'Shock-absorbing three-strand nylon, ideal for anchoring.',
    fullDesc:'Three-strand nylon anchor line with outstanding shock-absorption — essential for anchoring where sudden wave and wind loads must be absorbed without damage. Stretches to absorb shocks then returns to original form. Saltwater and UV resistant.',
    specs:{Diameter:'14 mm',Material:'Nylon (Polyamide)',Construction:'3-strand laid','WLL':'1,000 kg','Breaking Strength':'3,000 kg',Colour:'White','UV Resistance':'Good','Elongation':'Up to 25%'},
    tags:['14mm','Shock absorbing','Saltproof'], related:['p4','p6']
  },
  {
    id:'p6', name:'Floating Dock Line', cat:'marine',
    price:21.50, unit:'/ 10m', pricePerM:2.15, rating:4.5, reviews:88, badge:'',
    ropeClass:'rt-float', imgUrl:'/images/img2.jpg',
    shortDesc:'Buoyant rope that stays visible on the water surface.',
    fullDesc:'Polypropylene rope that floats on water — ideal for dock lines, safety throw lines, and water-sports where a floating line is essential. High-visibility colour ensures easy retrieval. Will not waterlog, tangle around propellers, or absorb contamination.',
    specs:{Diameter:'10 mm',Material:'Polypropylene (PP)',Construction:'Braided','WLL':'400 kg','Breaking Strength':'1,200 kg',Colour:'Hi-vis Yellow/Orange','Floats':'Yes','UV Resistance':'Good'},
    tags:['10mm','Floats','Hi-vis'], related:['p4','p5']
  },
  /* ——— Fabric ——— */
  {
    id:'p7', name:'Soft Cotton Braided Rope', cat:'fabric',
    price:12.90, unit:'/ 10m', pricePerM:1.29, rating:4.8, reviews:421, badge:'Bestseller',
    ropeClass:'rt-cotton', imgUrl:'/images/img7.webp',
    shortDesc:'Skin-friendly cotton rope for crafts, décor and macramé.',
    fullDesc:'Premium 100% natural cotton braided rope. Exceptionally soft to the touch — ideal for DIY crafts, home décor, macramé plant hangers, pet toys, and anywhere skin contact is likely. Holds knots cleanly and takes dye well. Natural cream, can be dyed with fabric dyes.',
    specs:{Diameter:'8 mm',Material:'100% Natural Cotton',Construction:'Braided','Safe Load':'150 kg',Colour:'Natural cream','Dyeable':'Yes','Washable':'Yes (30°C)',Finish:'Soft matte'},
    tags:['8mm','100% cotton','Soft touch'], related:['p8','p9']
  },
  {
    id:'p8', name:'Macramé Cord Bundle', cat:'fabric',
    price:9.50, unit:'/ 25m', pricePerM:0.38, rating:4.9, reviews:530, badge:'Top rated',
    ropeClass:'rt-macrame', imgUrl:'/images/img8.webp',
    shortDesc:'Fine twisted cotton cord for plant hangers and wall art.',
    fullDesc:'Three-strand twisted macramé cord in natural undyed cotton. Balanced twist allows clean unknotting for fringe and feather effects. A favourite for plant hangers, wall hangings, table runners, and dreamcatchers. Soft enough to work bare-handed for hours. Oeko-Tex certified.',
    specs:{Diameter:'4 mm',Material:'100% Natural Cotton',Construction:'3-strand twisted','Safe Load':'50 kg',Colour:'Natural off-white','Bundle':'25 m spool','Certification':'Oeko-Tex Standard 100'},
    tags:['4mm','Crafts','Natural'], related:['p7','p9']
  },
  {
    id:'p9', name:'Coloured Fabric Rope', cat:'fabric',
    price:15.90, unit:'/ 10m', pricePerM:1.59, rating:4.6, reviews:142, badge:'',
    ropeClass:'rt-color', imgUrl:'/images/img9.webp',
    shortDesc:'Vibrant dyed cotton rope for upholstery and design work.',
    fullDesc:'Colourful braided cotton rope available in 12 vibrant shades. Pre-dyed with low-impact textile dyes for strong, fade-resistant colour. Excellent for upholstery trims, curtain tie-backs, children\'s crafts, festival decoration, and any project needing a pop of colour.',
    specs:{Diameter:'6 mm',Material:'Dyed Cotton',Construction:'Braided',Colours:'12 options','Colour Fastness':'Grade 4–5 (ISO 105)','Washable':'Yes (30°C)','Safe Load':'100 kg',Finish:'Smooth braid'},
    tags:['6mm','12 colours','Washable'], related:['p7','p8']
  },
  /* ——— Climbing ——— */
  {
    id:'p10', name:'Dynamic Climbing Rope', cat:'climbing',
    price:129.00, unit:'/ 50m', pricePerM:2.58, rating:5.0, reviews:76, badge:'Certified',
    ropeClass:'rt-dynamic', imgUrl:'/images/img1.jpg',
    shortDesc:'CE/UIAA-certified dynamic rope for lead and top-rope climbing.',
    fullDesc:'Single dynamic climbing rope certified to CE EN892 and UIAA 101. The dynamic construction absorbs fall energy progressively, reducing peak forces on climber, belayer, and protection. Dry-treated sheath keeps weight down in wet conditions. Ideal for sport, trad, and alpine climbing.',
    specs:{Diameter:'9.8 mm',Material:'Nylon core + sheath',Type:'Single dynamic','UIAA Falls':'≥ 8','Impact Force':'8.9 kN','Elongation (1st fall)':'33%',Certifications:'CE EN892, UIAA 101',Treatment:'Dry treated core + sheath'},
    tags:['9.8mm','UIAA','Dynamic'], related:['p11','p12']
  },
  {
    id:'p11', name:'Static Rigging Rope', cat:'climbing',
    price:89.00, unit:'/ 50m', pricePerM:1.78, rating:4.8, reviews:64, badge:'',
    ropeClass:'rt-static', imgUrl:'/images/img4.jpg',
    shortDesc:'Low-stretch static line for hauling, rescue and abseiling.',
    fullDesc:'Type A static rope certified to CE EN1891 for rescue, caving, canyoning, and access work. Very low elongation (< 5%) makes it ideal for hauling systems, guided-rappel setups, and any application needing a taut system. Robust sheath resists abrasion on rocky surfaces.',
    specs:{Diameter:'11 mm',Material:'Nylon core + Polyester sheath',Type:'Static (Type A)','WLL':'1,500 kg','Breaking Strength':'3,600 kg','Elongation at 150kg':'< 5%',Certifications:'CE EN1891 Type A'},
    tags:['11mm','Static','Rescue'], related:['p10','p12']
  },
  {
    id:'p12', name:'Accessory Cord', cat:'climbing',
    price:11.00, unit:'/ 10m', pricePerM:1.10, rating:4.7, reviews:119, badge:'',
    ropeClass:'rt-cord', imgUrl:'/images/img7.webp',
    shortDesc:'Versatile cord for prusiks, slings and gear loops.',
    fullDesc:'Kernmantle accessory cord for building prusik loops, slings, gear management, and emergency backups. High strength-to-diameter ratio. Supple in cold conditions. Sold by the metre — build exactly the slings you need.',
    specs:{Diameter:'6 mm',Material:'Nylon kernmantle',Type:'Accessory cord','Breaking Strength':'700 kg',Colour:'Purple/Blue fleck',Certifications:'CE EN564','Use':'Prusiks, slings, gear'},
    tags:['6mm','Multi-use','Strong'], related:['p10','p11']
  },
];

/* helpers */
/**
 * Finds a product by its ID.
 * @param {string} id - The ID of the product to find.
 * @returns {Object|undefined} The product object if found, otherwise undefined.
 */
function findProduct(id){ return PRODUCTS.find(p=>p.id===id); }

/**
 * Gets the name of a category by its ID.
 * @param {string} id - The ID of the category.
 * @returns {string} The name of the category or the ID if not found.
 */
function catName(id){ return (CATEGORIES.find(c=>c.id===id)||{}).name||id; }

/**
 * Gets the full information object of a category by its ID.
 * @param {string} id - The ID of the category.
 * @returns {Object} The category object or an empty object if not found.
 */
function catInfo(id){ return CATEGORIES.find(c=>c.id===id)||{}; }
