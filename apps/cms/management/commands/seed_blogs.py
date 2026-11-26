"""Seed 15 Nyanopan articles with complete SEO metadata."""

from django.core.management.base import BaseCommand

from apps.catalog.models import Product
from apps.cms.models import Blog, BlogCategory


STOREFRONT_URL = "https://nyanopan.vercel.app"
ROBOTS = Blog.RobotsChoices.INDEX_FOLLOW_MAX_IMAGE
TWITTER_CARD = Blog.TwitterCardChoices.SUMMARY_LARGE_IMAGE

ARTICLES = [
    {
        "slug": "choosing-wool-slippers-for-everyday-comfort",
        "title": "Choosing Wool Slippers for Everyday Comfort",
        "category": "Shoes",
        "excerpt": "A practical guide to choosing comfortable wool slippers for the rooms and routines you use every day.",
        "opening": "The right pair of slippers should feel easy from the first step. Think about where you wear them, how warm you like your feet, and the kind of sole your floors need.",
        "heading": "Start with where you will wear them",
        "body": "A soft leather sole glides quietly across smooth indoor floors. A crepe rubber sole offers more grip for steps onto a patio or garden path. Wool felt gives either style a breathable upper that settles gently around the foot.",
        "tip": "Choose the sole for your usual surface, then check the size guide for a relaxed, secure fit.",
        "keywords": ["wool slippers", "comfortable house shoes", "slipper buying guide"],
        "tags": ["wool", "comfort", "buying guide"],
        "image_alt": "Hand-felted wool slipper showing its natural felt upper",
        "featured": True,
    },
    {
        "slug": "how-to-care-for-wool-felt-slippers",
        "title": "How to Care for Wool Felt Slippers",
        "category": "Wool Care",
        "excerpt": "Simple everyday care helps wool felt slippers stay fresh, comfortable, and ready for many more quiet steps.",
        "opening": "Wool felt is made for regular wear, and a little gentle care goes a long way. Give slippers room to air after wearing and keep them away from unnecessary heat.",
        "heading": "A gentle care routine",
        "body": "Let moisture evaporate naturally before putting slippers away. Brush away dry dust with a soft brush. For a small mark, dab gently with a clean cloth and cool water instead of rubbing the felt.",
        "tip": "Air dry at room temperature; direct high heat can change the shape and feel of wool felt.",
        "keywords": ["wool slipper care", "clean wool felt", "felt shoe care"],
        "tags": ["care", "wool felt", "maintenance"],
        "image_alt": "Natural wool felt texture on a handcrafted slipper",
        "featured": True,
    },
    {
        "slug": "what-makes-hand-felted-slippers-different",
        "title": "What Makes Hand-Felted Slippers Different?",
        "category": "Craftsmanship",
        "excerpt": "Explore the hands-on felting process that turns mountain wool, warm water, and careful shaping into a seamless slipper.",
        "opening": "Hand felting builds the slipper from wool fibres rather than stitching together a collection of upper panels. Water, warmth, and repeated pressure help the fibres lock together around a foot-shaped form.",
        "heading": "Shaped by patient, practical work",
        "body": "At the Kathmandu atelier, makers wash the wool, felt it by hand, shape it on a wooden last, and let it dry. The one-piece upper has no interior seams across the foot, creating a smooth and simple feel.",
        "tip": "Look for the maker's signature: it connects each finished pair to the hands that shaped it.",
        "keywords": ["hand felted slippers", "handmade wool footwear", "Nepal craftsmanship"],
        "tags": ["craftsmanship", "handmade", "Kathmandu"],
        "image_alt": "Handcrafted slipper made from a seamless piece of wool felt",
        "featured": True,
    },
    {
        "slug": "why-wool-feels-comfortable-through-the-seasons",
        "title": "Why Wool Feels Comfortable Through the Seasons",
        "category": "Wool Care",
        "excerpt": "Wool's natural structure helps create a comfortable feel in changing temperatures and during barefoot wear.",
        "opening": "Wool is valued for more than warmth. Its crimped fibres hold small pockets of air and can absorb moisture vapour, helping footwear feel comfortable across changing indoor conditions.",
        "heading": "A natural fibre with a useful structure",
        "body": "In a slipper, a wool felt upper provides a soft layer around the foot without relying on synthetic fleece. Comfort still depends on fit, room temperature, and how active you are, so choose the weight and shape that suit your home.",
        "tip": "If your feet feel warm after wearing, let the slippers air before the next use.",
        "keywords": ["wool slippers all seasons", "natural wool comfort", "breathable wool footwear"],
        "tags": ["wool", "natural fibres", "comfort"],
        "image_alt": "Soft wool felt upper designed for comfortable everyday wear",
        "featured": False,
    },
    {
        "slug": "leather-or-crepe-rubber-slipper-soles",
        "title": "Leather or Crepe Rubber: Which Slipper Sole Is Right for You?",
        "category": "Shoes",
        "excerpt": "Compare quiet leather soles for smooth indoor floors with grippy crepe rubber soles for steps outside.",
        "opening": "The sole changes where a slipper feels most at home. Consider your flooring, how often you step outdoors, and whether quiet movement or extra traction matters more to you.",
        "heading": "Two soles, two everyday uses",
        "body": "Vegetable-tanned leather soles are designed for a smooth indoor glide across wood and tile. Natural crepe rubber provides more traction and suits short trips onto a patio or similar surface. Neither sole replaces outdoor footwear for rough or wet terrain.",
        "tip": "Choose leather for quiet indoor floors or crepe rubber when you want added grip near the home.",
        "keywords": ["leather sole slippers", "crepe rubber slippers", "indoor slipper soles"],
        "tags": ["soles", "leather", "crepe rubber"],
        "image_alt": "Wool slipper with a durable sole for everyday use",
        "featured": True,
    },
    {
        "slug": "finding-the-right-fit-for-wool-slippers",
        "title": "Finding the Right Fit for Wool Slippers",
        "category": "Shoes",
        "excerpt": "Use these fit tips to choose wool slippers that feel secure without squeezing your toes.",
        "opening": "A good slipper fit holds the heel comfortably and leaves the toes room to rest. Wool felt can soften with wear, so begin with the size guidance rather than choosing a tight fit.",
        "heading": "Check length, width, and heel hold",
        "body": "Measure both feet while standing and use the larger measurement against the brand's size chart. Try slippers with the socks you expect to wear, and walk on a clean indoor surface to notice any slipping or pressure.",
        "tip": "If you are between sizes, compare the brand's recommendations and consider how much toe room you prefer.",
        "keywords": ["wool slipper sizing", "slipper fit guide", "how slippers should fit"],
        "tags": ["fit", "sizing", "buying guide"],
        "image_alt": "Wool slippers shaped to follow the natural outline of the foot",
        "featured": False,
    },
    {
        "slug": "from-mountain-wool-to-a-finished-slipper",
        "title": "From Mountain Wool to a Finished Slipper",
        "category": "Craftsmanship",
        "excerpt": "Follow the main steps that take wool from careful washing and felting to a shaped, finished slipper.",
        "opening": "A finished slipper begins with selected wool and a sequence of patient workshop steps. Each stage changes the loose fibre into a dense felt upper shaped for the foot.",
        "heading": "Washing, felting, shaping, and drying",
        "body": "Makers wash the wool, felt it with warm water and hand pressure, then shape the growing form over a wooden last. After shaping, the slipper dries before the sole and finishing details are completed.",
        "tip": "Small differences in handmade felt are part of the material and process; each pair has its own character.",
        "keywords": ["wool slipper making process", "hand felting wool", "handmade slippers Nepal"],
        "tags": ["process", "wool", "makers"],
        "image_alt": "Hand-felted wool slipper made in a Kathmandu workshop",
        "featured": False,
    },
    {
        "slug": "keeping-wool-slippers-fresh-between-wears",
        "title": "Keeping Wool Slippers Fresh Between Wears",
        "category": "Wool Care",
        "excerpt": "Airing, dry storage, and gentle spot care can keep wool slippers pleasant between wears.",
        "opening": "Freshness usually starts with giving slippers time to breathe. After wearing, leave them in a dry, ventilated spot instead of placing them straight into a closed cupboard.",
        "heading": "Let air do most of the work",
        "body": "Rotate between pairs if you wear slippers all day. Remove loose dust with a soft brush, and avoid fragrance sprays that may leave residue on wool. Before storage, make sure the felt is fully dry.",
        "tip": "A breathable storage bag protects slippers from dust while still allowing air circulation.",
        "keywords": ["keep wool slippers fresh", "air wool shoes", "store felt slippers"],
        "tags": ["freshness", "care", "storage"],
        "image_alt": "Breathable wool felt footwear for relaxed home routines",
        "featured": False,
    },
    {
        "slug": "a-thoughtful-gift-guide-to-wool-slippers",
        "title": "A Thoughtful Gift Guide to Wool Slippers",
        "category": "Product",
        "excerpt": "A warm, useful gift starts with choosing the right style, sole, and size for the person receiving it.",
        "opening": "A pair of handmade slippers can be a practical gift for someone who enjoys comfort at home. A little attention to size and daily habits makes the choice more personal.",
        "heading": "Make the choice personal",
        "body": "Consider whether the recipient mostly walks on smooth indoor floors or steps outside briefly. Check their usual shoe size against the available size chart, and choose a colour that fits their everyday style.",
        "tip": "When you are unsure of fit, include a gift receipt or check the store's current exchange policy before ordering.",
        "keywords": ["wool slipper gift", "handmade footwear gift", "comfort gift ideas"],
        "tags": ["gifting", "handmade", "comfort"],
        "image_alt": "Handcrafted wool slippers ready to be wrapped as a thoughtful gift",
        "featured": False,
    },
    {
        "slug": "indoor-slippers-for-steps-outside",
        "title": "Can Indoor Slippers Handle a Step Outside?",
        "category": "Shoes",
        "excerpt": "Learn why sole choice matters when moving from indoor floors to a patio or garden step.",
        "opening": "Some homes make it convenient to step onto a veranda or patio without changing footwear. In that case, sole material matters as much as the upper.",
        "heading": "Match footwear to the surface",
        "body": "Crepe rubber soles provide more grip than soft leather soles and are better suited to short, careful steps outside on a dry surface. Wool felt is not designed to be soaked, and slippers are not substitutes for weatherproof outdoor shoes.",
        "tip": "Keep wool slippers dry and use dedicated outdoor footwear for rain, mud, or long walks.",
        "keywords": ["indoor outdoor slippers", "rubber sole house shoes", "slippers for patio"],
        "tags": ["soles", "indoor footwear", "rubber"],
        "image_alt": "Slipper sole selected for grip on a home patio",
        "featured": False,
    },
    {
        "slug": "how-to-store-wool-felt-footwear",
        "title": "How to Store Wool Felt Footwear",
        "category": "Wool Care",
        "excerpt": "Store slippers clean, dry, and away from excess heat to help preserve their shape between seasons.",
        "opening": "When warmer weather arrives, prepare wool slippers for storage by making sure they are clean and completely dry. A little preparation makes them easier to reach for later.",
        "heading": "Choose a cool, dry place",
        "body": "Brush away dust, allow any moisture to evaporate, and store slippers in a breathable container. Avoid airtight plastic for long periods and keep the pair away from direct sun or a heat source.",
        "tip": "Place both slippers together and avoid stacking heavy objects on top, which can flatten the felt.",
        "keywords": ["store wool slippers", "seasonal footwear storage", "protect wool felt shoes"],
        "tags": ["storage", "seasonal care", "wool felt"],
        "image_alt": "Wool felt slippers stored neatly between seasons",
        "featured": False,
    },
    {
        "slug": "the-makers-behind-each-hand-felted-pair",
        "title": "The Makers Behind Each Hand-Felted Pair",
        "category": "Craftsmanship",
        "excerpt": "Meet the care and skill involved in making slippers by hand in a small Kathmandu workshop.",
        "opening": "Handmade footwear carries the work of the people who shape, finish, and inspect it. Nyanopan slippers are made in a small Kathmandu workshop where the process relies on hands-on skill.",
        "heading": "A process guided by people",
        "body": "From washing wool to shaping felt around a wooden last, makers guide each stage. The finished pair carries small details of its making, including a stitched maker signature on the slipper.",
        "tip": "Explore the Our Makers page to learn more about the people and workshop behind Nyanopan.",
        "keywords": ["Nyanopan makers", "Kathmandu slipper workshop", "handmade wool slippers Nepal"],
        "tags": ["makers", "Kathmandu", "craft"],
        "image_alt": "A handcrafted Nyanopan slipper representing the work of its maker",
        "featured": False,
    },
    {
        "slug": "natural-materials-in-everyday-footwear",
        "title": "Natural Materials in Everyday Footwear",
        "category": "Product",
        "excerpt": "Understand the role wool, vegetable-tanned leather, and crepe rubber can play in a thoughtfully made slipper.",
        "opening": "Materials shape how footwear feels, wears, and fits into daily life. Nyanopan slippers bring together wool felt uppers with a choice of leather or crepe rubber soles.",
        "heading": "Each material has a different job",
        "body": "Wool forms the soft upper. Vegetable-tanned leather creates a quiet sole for indoor floors, while natural crepe rubber offers a grippier option for brief steps outside. Choosing materials thoughtfully also means caring for them appropriately.",
        "tip": "Check the material and care details for the exact style you choose, since sole options differ.",
        "keywords": ["natural material slippers", "wool leather rubber footwear", "sustainable slippers"],
        "tags": ["materials", "wool", "leather", "rubber"],
        "image_alt": "Wool felt slipper made with carefully selected natural materials",
        "featured": False,
    },
    {
        "slug": "the-quiet-comfort-of-seamless-felt",
        "title": "The Quiet Comfort of Seamless Felt Construction",
        "category": "Product",
        "excerpt": "A seamless wool felt upper keeps the inside of a slipper smooth and simple against the foot.",
        "opening": "Some slippers are assembled from several stitched panels. Hand-felted slippers take another route: the upper forms as one continuous piece around a foot-shaped last.",
        "heading": "Fewer seams, a simpler feel",
        "body": "Without interior panel seams across the upper, the felt feels smooth around the foot. The fit still matters, and choosing the correct size helps the shape sit comfortably without pressure.",
        "tip": "Try slippers on a clean floor at home and give the wool a little time to settle around your foot.",
        "keywords": ["seamless wool slippers", "felt slipper comfort", "hand felted footwear"],
        "tags": ["seamless", "comfort", "design"],
        "image_alt": "One-piece wool felt upper with a smooth, seamless interior",
        "featured": True,
    },
    {
        "slug": "five-small-ways-to-make-slippers-last-longer",
        "title": "Five Small Ways to Help Your Slippers Last Longer",
        "category": "Wool Care",
        "excerpt": "Five easy habits—airing, brushing, drying, storing, and choosing the right sole—can support longer slipper wear.",
        "opening": "Good care does not need to be complicated. A few small habits can help preserve the shape and feel of wool felt slippers through regular use.",
        "heading": "Five habits worth keeping",
        "body": "Air slippers after wearing, brush away dry dust, spot clean gently, let them dry naturally, and choose a sole that matches the surface. These steps reduce avoidable wear without harsh cleaning or unnecessary products.",
        "tip": "The most useful habit is simple: keep wool felt dry and let it breathe between wears.",
        "keywords": ["make slippers last longer", "wool slipper maintenance", "felt footwear care tips"],
        "tags": ["care tips", "maintenance", "wool"],
        "image_alt": "Well-cared-for wool slippers ready for daily use",
        "featured": False,
    },
]


class Command(BaseCommand):
    help = "Create or update 15 Nyanopan blog posts with SEO metadata."

    def handle(self, *args, **options):
        categories = {
            name: BlogCategory.objects.get_or_create(name=name)[0]
            for name in {article["category"] for article in ARTICLES}
        }
        image_urls = self._image_urls()
        created_count = 0
        updated_count = 0

        for index, article in enumerate(ARTICLES):
            slug = article["slug"]
            image_url = image_urls[index % len(image_urls)]
            canonical_url = f"{STOREFRONT_URL}/blog/{slug}"
            title = article["title"]
            description = article["excerpt"]
            tags = article["tags"]
            keywords = article["keywords"]
            image_alt = article["image_alt"]
            image_title = title
            image_caption = article["excerpt"]
            html_content = (
                f"<p>{article['opening']}</p>"
                f"<h2>{article['heading']}</h2>"
                f"<p>{article['body']}</p>"
                f"<p><strong>Tip:</strong> {article['tip']}</p>"
            )
            defaults = {
                "title": title,
                "excerpt": article["excerpt"],
                "category": categories[article["category"]],
                "image": image_url,
                "image_title": image_title,
                "image_alt": image_alt,
                "image_caption": image_caption,
                "content": html_content,
                "tags": tags,
                "is_featured": article["featured"],
                "is_published": True,
                "meta_title": f"{title} | Nyanopan"[:255],
                "meta_description": description[:320],
                "meta_keywords": keywords,
                "canonical_url": canonical_url,
                "meta_robots": ROBOTS,
                "og_title": title,
                "og_description": description[:320],
                "og_url": canonical_url,
                "og_image": image_url,
                "twitter_card": TWITTER_CARD,
                "twitter_title": title,
                "twitter_description": description[:320],
                "twitter_image": image_url,
            }
            _, created = Blog.objects.update_or_create(
                slug=slug,
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_count} new blogs; updated {updated_count} existing seed blogs."
            )
        )

    def _image_urls(self):
        storage = Blog._meta.get_field("image").storage
        image_urls = []
        for image_ref in Product.objects.exclude(feature_image="").values_list(
            "feature_image", flat=True
        ):
            if image_ref and image_ref not in image_urls:
                image_urls.append(image_ref)
        if not image_urls:
            image_urls = list(
                Blog.objects.exclude(image="")
                .values_list("image", flat=True)
                .distinct()
            )
        if not image_urls:
            raise RuntimeError("No existing product or blog image is available for the seed posts.")
        return image_urls
