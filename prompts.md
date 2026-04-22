# PROMPT 1A
## **Structured Product Input**
```
**TASK:** Product Data Extraction and Structuring

Analyze all provided unstructured product inputs:
• packaging text
• specification sheets
• URLs
• documents
• chat text
• product label images

Extract structured product information.

**RULES**
1. Confirm values only from provided sources.
2. Do NOT invent attributes or values.
3. If a known value cannot be confirmed → "Unconfirmed".
4. Extract ALL discovered attributes as attribute-value pairs.
5. Return ONLY valid JSON.
6. reference_tag must be read from workflow_state.json and preserved unchanged.

**OUTPUT SCHEMA**
{
 "reference_tag": "",
 "product_category": "",
 "product_profile": {
   "brand": "",
   "product_name": "",
   "model": "",
   "color": ""
 },

 "core_features": [],

 "attributes": {
   "attribute_name": "value"
 },

 "additional_attributes": {
   "attribute_name": "value"
 },

 "package_contents": [],

 "product_summary": ""
}

**TASK BOUNDARY**
Execute only this extraction step.

**OUTPUT RULE**
Return only valid JSON.

**Use the following PRODUCT DATA as provided in the current input bundle:**
- Product metadata
- Packaging text
- Specification sheets
- URLs
- Documents
- Chat text
- Product label images
- Product box images

Extract only what is present in the provided sources.
Do not assume a category or invent missing data.
```

---
# PROMPT 1B
```
**TASK:** Visual Product Identity Extraction

Analyze ALL provided product images.

Images may include multiple angles such as:
• front_3q_left
• front_3q_right
• rear_3q
• left_side
• right_side
• top_view
• bottom_view
• accessories_layout
• detail_closeup

Identify the view type of each image and extract visual grounding data.

**VISUAL_GROUNDING_BLOCK**

Return JSON:

{
 "image_views": {
   "front_3q_left": "",
   "front_3q_right": "",
   "rear_3q": "",
   "left_side": "",
   "right_side": "",
   "top_view": "",
   "bottom_view": "",
   "detail_closeup": "",
   "accessories_layout": ""
 },

 "visual_identity": {
   "product_type": "",
   "dominant_color": "",
   "materials": "",
   "primary_components": []
 },

 "object_layout_map": {
   "component_positions": {}
 },

 "lighting_profile": {
   "lighting_type": "",
   "shadow_behavior": "",
   "reflection_style": ""
 },

 "camera_profile": {
   "camera_angle": "",
   "orientation": "",
   "lens_style": ""
 },

 "product_geometry": {
   "shape_description": "",
   "proportions": "",
   "relative_dimensions": ""
 }
}

**RULES**
1. Extract only visually observable information.
2. Do NOT invent details.
3. Preserve spatial relationships between components.
4. Return ONLY valid JSON.

**TASK BOUNDARY**
Execute only this visual extraction step.

**OUTPUT RULE**
Return only valid JSON.
```

---
# PROMPT 2
## **Amazon Listing Strategy**
```
**TASK:** Amazon Product Title Generation

**INPUT**
Use the structured dataset and visual grounding information from workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- package_contents
- visual_identity
- product_geometry

**OBJECTIVE**
Generate a high-conversion Amazon product title optimized for search visibility and customer readability.

**RULES**
1. Maximum length: 200 characters (including spaces).
2. Use only attributes present in workflow_state.json.
3. Do NOT invent specifications or features.
4. Avoid keyword stuffing and repeated words.
5. Avoid promotional phrases (e.g., “Best Seller”, “Free Shipping”).
6. Do NOT include special characters unless part of the brand name.
7. Prioritize the most important attributes from:
   - product_profile
   - core_features
   - attributes
8. Ensure the title clearly identifies the product.

**TITLE STRUCTURE GUIDELINE**
Brand + Product Type + Key Feature + Important Specification + Primary Benefit

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "amazon_product_title": ""
}
```

---
# PROMPT 3
```
**TASK:** Amazon Bullet Point Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- package_contents
- visual_identity
- product_geometry

**OBJECTIVE**
Generate optimized Amazon bullet points that clearly communicate the product’s key benefits and features.

**RULES**
1. Use only information present in workflow_state.json.
2. Do NOT invent specifications or features.
3. Focus on customer benefits supported by real features.
4. Ensure each bullet highlights a different selling point.
5. Avoid promotional language, pricing, or guarantees.
6. Keep bullets concise and mobile-readable.
7. Maximum bullets: 5.

**STRUCTURE GUIDELINE**
Start with a short BENEFIT HEADLINE followed by a concise supporting explanation.

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "amazon_bullet_points": [
   "BENEFIT HEADLINE — Supporting feature explanation",
   "BENEFIT HEADLINE — Supporting feature explanation",
   "BENEFIT HEADLINE — Supporting feature explanation",
   "BENEFIT HEADLINE — Supporting feature explanation",
   "BENEFIT HEADLINE — Supporting feature explanation"
 ]
}
```

---
# PROMPT 4
```
**TASK:** Amazon Product Description Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- package_contents
- visual_identity
- product_geometry
- amazon_bullet_points

**OBJECTIVE**
Write a persuasive Amazon product description that clearly explains the product’s purpose, benefits, and use cases while maintaining accuracy and readability.

**RULES**
1. Use only information contained in workflow_state.json.
2. Do NOT invent features or specifications.
3. Focus on customer benefits supported by real product features.
4. Expand on the key ideas introduced in the bullet points.
5. Write in clear, natural language suitable for shoppers.
6. Avoid exaggerated claims, promotional phrases, or pricing information.
7. Target length: 150–300 words.

**DESCRIPTION GUIDELINES**
The description should:
• Explain what the product is and who it is for  
• Highlight key benefits and real-world use cases  
• Reinforce reliability, safety, and usability  
• Maintain keyword relevance for Amazon search

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "amazon_product_description": ""
}
```

---
# PROMPT 5
```
**TASK:** Amazon Backend Search Terms Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- product_geometry
- amazon_product_title
- amazon_bullet_points
- amazon_product_description

**OBJECTIVE**
Generate optimized Amazon backend search terms that improve product discoverability in Amazon search results.

**RULES**
1. Do NOT repeat words already used in the title, bullet points, or description.
2. Use relevant search terms, synonyms, alternate phrases, and long-tail search variations.
3. Do NOT include brand names or competitor brand names.
4. Do NOT use punctuation or special characters.
5. Avoid filler words (a, an, the, with, for, and, of).
6. Separate keywords using spaces only.
7. Focus only on terms directly relevant to the product.

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "amazon_backend_search_terms": ""
}
```

---
# PROMPT 6
```
**TASK:** Customer Search Intent Keyword Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- amazon_product_title
- amazon_bullet_points
- amazon_product_description

**OBJECTIVE**
Generate customer search intent keywords representing the types of queries shoppers would likely type into Amazon when looking for this product.

**RULES**
1. Use only product information contained in workflow_state.json.
2. Do NOT invent product features or specifications.
3. Do NOT repeat the exact product title.
4. Do NOT include competitor brand names.
5. Use natural shopper language.
6. Include both short-tail and long-tail search phrases.
7. Prioritize keywords indicating purchase intent.

**KEYWORD TYPES**
• Generic product searches  
• Feature-based searches  
• Problem-solution searches  
• Use-case searches  
• Long-tail buyer intent searches

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "customer_search_intent_keywords": {
   "generic_searches": [],
   "feature_searches": [],
   "problem_solution_searches": [],
   "use_case_searches": [],
   "long_tail_buyer_searches": []
 }
}
```

---
# PROMPT 7
```
**TASK:** Amazon A+ Content Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- amazon_product_title
- amazon_bullet_points
- amazon_product_description
- visual_identity
- product_geometry

**OBJECTIVE**
Generate structured Amazon A+ Content text designed to support product images and visually explain the product’s key benefits.

**RULES**
1. Use only information contained in workflow_state.json.
2. Do NOT invent product features or specifications.
3. Focus on customer benefits supported by real product attributes.
4. Keep paragraphs concise for visual modules.
5. Avoid exaggerated claims, guarantees, or promotional hype.
6. Write text that complements product images rather than repeating the same information.

**CONTENT STRUCTURE**
Brand Story:
Introduce the brand and communicate its mission, values, and commitment to product quality.

Feature Section 1:
Highlight the most important product benefit and how it solves a customer problem.

Feature Section 2:
Explain another major feature and its practical value for the user.

Feature Section 3:
Explain a technical capability and why it matters to the customer.

Feature Section 4:
Highlight usability, reliability, or everyday convenience.

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "amazon_aplus_content": {
   "seller_or_brand_story": "",
   "feature_section_1": {
     "headline": "",
     "supporting_text": ""
   },
   "feature_section_2": {
     "headline": "",
     "supporting_text": ""
   },
   "feature_section_3": {
     "headline": "",
     "supporting_text": ""
   },
   "feature_section_4": {
     "headline": "",
     "supporting_text": ""
   }
 }
}
```

---
# PROMPT 8
```
**TASK:** Technical Specifications Section Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- package_contents
- visual_identity
- product_geometry

**OBJECTIVE**
Generate a clear technical specification list formatted for the Amazon Product Details section.

**RULES**
1. Use only information contained in workflow_state.json.
2. Do NOT invent specifications or technical values.
3. Present information as factual attribute-value pairs.
4. Use neutral language (no marketing claims).
5. Ensure the format is easy to scan and compare.
6. Include all relevant attributes discovered in the dataset.

**STRUCTURE GUIDELINE**
Organize specifications using attribute: value formatting.

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "technical_specifications": {
   "Brand": "",
   "Product Name": "",
   "Model": "",
   "Color": "",
   "Attributes": {
     "attribute_name": "value"
   }
 },
 "package_contents": []
}
```

---
# PROMPT 9
```
**TASK:** Customer FAQ Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- package_contents
- amazon_product_title
- amazon_bullet_points
- amazon_product_description
- visual_identity
- product_geometry

**OBJECTIVE**
Generate realistic customer questions and clear answers that shoppers might ask before purchasing the product.

**RULES**
1. Use only information contained in workflow_state.json.
2. Do NOT invent features or specifications.
3. Focus on questions real shoppers commonly ask before buying.
4. Ensure answers are clear, concise, and helpful.
5. Avoid promotional language or exaggerated claims.
6. Each FAQ must address a different customer concern.
7. Generate exactly 5 FAQs.

**QUESTION STRATEGY**
Base questions on common buyer concerns such as:
- product purpose
- installation or setup
- compatibility or usage scenarios
- technical capabilities
- reliability or durability

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "customer_faq": [
   {
     "question": "",
     "answer": ""
   },
   {
     "question": "",
     "answer": ""
   },
   {
     "question": "",
     "answer": ""
   },
   {
     "question": "",
     "answer": ""
   },
   {
     "question": "",
     "answer": ""
   }
 ]
}
```

---
# PROMPT 10
```
**TASK:** Social Media Post Creation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- core_features
- attributes
- additional_attributes
- amazon_product_title
- amazon_bullet_points
- amazon_product_description
- customer_search_intent_keywords
- visual_identity

**OBJECTIVE**
Create engaging social media posts suitable for Facebook and Instagram that highlight the product’s value and solve a customer pain point.

**RULES**
1. Use only information contained in workflow_state.json.
2. Do NOT invent features or specifications.
3. Begin captions with a strong hook that addresses a real customer problem.
4. Keep captions concise and engaging.
5. Use natural language suitable for social media audiences.
6. Provide discoverability tags and relevant hashtags.
7. Avoid exaggerated claims or promotional hype.

**POST STRATEGY**
Each post should focus on a different angle:
• Problem solved by the product
• Key feature or benefit
• Real-world use case

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "social_media_posts": [
   {
     "post_number": 1,
     "caption_title": "",
     "caption_text": "",
     "tags": [],
     "hashtags": []
   },
   {
     "post_number": 2,
     "caption_title": "",
     "caption_text": "",
     "tags": [],
     "hashtags": []
   },
   {
     "post_number": 3,
     "caption_title": "",
     "caption_text": "",
     "tags": [],
     "hashtags": []
   }
 ]
}
```

---
# PROMPT 11
## **Amazon Image Strategy (7 Images + 1)**
```
**TASK:** Image 1 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- visual_identity
- object_layout_map
- lighting_profile
- camera_profile
- product_geometry
- image_views

**OBJECTIVE**
Generate the image-generation prompt for Image 1 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 1 → What is this product?

**IMAGE ROLE**
Hero Product Image (Amazon main image)

**AMAZON IMAGE RULES**
1. Pure white background (RGB 255,255,255)
2. Only the product and included accessories
3. No text, icons, badges, or graphics
4. Product fills approximately 85% of the frame
5. Entire product must be visible
6. Professional lighting and realistic product appearance
7. Accurate representation of the real product

**IMAGE FORMAT**
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition
- Product centered and dominant in frame

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 1,
   "image_type": "Hero Product Image",
   "buyer_question": "What is this product?",
   "layout_description": "",
   "headline_text": "N/A",
   "supporting_text": "N/A",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 12
```
**TASK:** Image 1 Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- visual_identity
- object_layout_map
- lighting_profile
- camera_profile
- product_geometry
- image_views
- image_strategy

**OBJECTIVE**
Generate Image 1 for the Amazon listing using the previously generated prompt.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 1 → What is this product?

**IMAGE ROLE**
Hero Product Image (Amazon main image)

**AMAZON IMAGE RULES**
1. Pure white background (RGB 255,255,255)
2. Only the product and included accessories
3. No text, logos, icons, badges, graphics, or watermarks
4. Product must fill approximately 85–95% of the frame
5. Entire product must be visible
6. Image must accurately represent the product
7. Professional studio lighting

**IMAGE FORMAT**
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition
- Ultra-sharp commercial product photography
- Product centered in frame

**VISUAL STYLE**
- Studio product photography
- Soft diffused lighting
- Realistic materials and reflections
- Clean e-commerce aesthetic
- Subtle soft shadow allowed

**STYLE LOCK EXTRACTION**
After generating the image, extract a reusable style profile to maintain consistency across the remaining images.

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 1,
   "image_type": "Hero Product Image",
   "image_generation_prompt": ""
 },

 "image_style_lock": {
   "lighting": "",
   "camera_lens": "",
   "shadow_style": "",
   "product_scale": "",
   "background": "pure white",
   "color_profile": ""
 }
}
```

---
# PROMPT 13
```
**TASK:** Image 2 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock

**OBJECTIVE**
Generate the image-generation prompt for Image 2 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 2 → Why do I need this product?

**IMAGE ROLE**
Feature / Core Benefit Image

**AMAZON IMAGE RULES**
1. Product must be clearly visible and accurately represented.
2. Text overlays and infographics are allowed for secondary images.
3. Graphics must explain real product features or benefits.
4. Do not misrepresent the product or show non-included accessories.
5. Maintain professional image quality and clarity.

**IMAGE FORMAT**
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

**STYLE CONSISTENCY**
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 2,
   "image_type": "Core Benefit Image",
   "buyer_question": "Why do I need this product?",
   "layout_description": "",
   "headline_text": "",
   "supporting_text": "",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 14
```
**TASK:** Image 2 Generation

INPUT
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_strategy
- image_style_lock

**OBJECTIVE**
Generate Image 2 for the Amazon listing based on the previously created prompt.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 2 → Why do I need this product?

**IMAGE ROLE**
Core Benefit / Feature Image

AMAZON IMAGE RULES
1. Product must be clearly visible and accurately represented.
2. Secondary images may include text overlays and infographics.
3. Graphics must represent real product features only.
4. Do not show accessories not included with the product.
5. Maintain professional quality and readability.

**IMAGE FORMAT**
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

**STYLE CONSISTENCY**
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 2,
   "image_type": "Core Benefit Image",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 15
```
**TASK:** Image 3 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock

**OBJECTIVE**
Generate the image-generation prompt for Image 3 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 3 → What problem does this product solve?

**IMAGE ROLE**
Problem → Solution Feature Image

AMAZON IMAGE RULES
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, text overlays, and icons.
3. Graphics must represent real product features only.
4. Do not show accessories not included with the product.
5. Maintain professional visual quality.

IMAGE FORMAT
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

STYLE CONSISTENCY
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

WORKFLOW MODE
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

OUTPUT FORMAT (JSON)

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 3,
   "image_type": "Problem Solution Image",
   "buyer_question": "What problem does this product solve?",
   "layout_description": "",
   "headline_text": "",
   "supporting_text": "",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 16
```
**TASK:** Image 3 Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_style_lock
- image_strategy

**OBJECTIVE**
Generate Image 3 for the Amazon listing using the prepared image strategy.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 3 → What problem does this product solve?

**IMAGE ROLE**
Problem → Solution Feature Image

**AMAZON IMAGE RULES**
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, icons, and text overlays.
3. Visual elements must represent real product features.
4. Do not depict accessories not included with the product.
5. Maintain professional image quality.

**IMAGE FORMAT**
Resolution: 1080 × 1920  
Aspect Ratio: 9:16  
Vertical composition

**STYLE CONSISTENCY**
Maintain the following parameters from workflow_state.json:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 3,
   "image_type": "Problem Solution Image",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 17
```
**TASK:** Image 4 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock

**OBJECTIVE**
Generate the image-generation prompt for Image 4 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 4 → When would I use this product?

**IMAGE ROLE**
Lifestyle / Real-World Use Image

AMAZON IMAGE RULES
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, text overlays, and icons.
3. Graphics must represent real product features only.
4. Do not show accessories not included with the product.
5. Maintain professional visual quality.

IMAGE FORMAT
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

STYLE CONSISTENCY
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

WORKFLOW MODE
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

OUTPUT FORMAT (JSON)

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 4,
   "image_type": "Lifestyle Use Image",
   "buyer_question": "When would I use this product?",
   "layout_description": "",
   "headline_text": "",
   "supporting_text": "",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 18
```
**TASK:** Image 4 Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_style_lock
- image_strategy

**OBJECTIVE**
Generate Image 4 for the Amazon listing using the prepared image strategy.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 4 → When would I use this product?

**IMAGE ROLE**
Lifestyle / Real-World Use Image

**AMAZON IMAGE RULES**
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, icons, and text overlays.
3. Visual elements must represent real product features.
4. Do not depict accessories not included with the product.
5. Maintain professional image quality.

**IMAGE FORMAT**
Resolution: 1080 × 1920  
Aspect Ratio: 9:16  
Vertical composition

**STYLE CONSISTENCY**
Maintain the following parameters from workflow_state.json:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 4,
   "image_type": "Lifestyle Use Image",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 19
```
**TASK:** Image 5 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock

**OBJECTIVE**
Generate the image-generation prompt for Image 5 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 5 → What technology makes this product better?

**IMAGE ROLE**
Technology / Capability Feature Image

AMAZON IMAGE RULES
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, text overlays, and icons.
3. Graphics must represent real product features only.
4. Do not show accessories not included with the product.
5. Maintain professional visual quality.

IMAGE FORMAT
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

STYLE CONSISTENCY
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

WORKFLOW MODE
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

OUTPUT FORMAT (JSON)

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 5,
   "image_type": "Technology Feature Image",
   "buyer_question": "What technology makes this product better?",
   "layout_description": "",
   "headline_text": "",
   "supporting_text": "",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 20
```
**TASK:** Image 5 Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_style_lock
- image_strategy

**OBJECTIVE**
Generate Image 5 for the Amazon listing using the prepared image strategy.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 5 → What technology makes this product better?

**IMAGE ROLE**
Technology / Capability Feature Image

**AMAZON IMAGE RULES**
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, icons, and text overlays.
3. Visual elements must represent real product features.
4. Do not depict accessories not included with the product.
5. Maintain professional image quality.

**IMAGE FORMAT**
Resolution: 1080 × 1920  
Aspect Ratio: 9:16  
Vertical composition

**STYLE CONSISTENCY**
Maintain the following parameters from workflow_state.json:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 5,
   "image_type": "Technology / Capability Feature Image",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 21
```
**TASK:** Image 6 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock

**OBJECTIVE**
Generate the image-generation prompt for Image 6 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 6 → How easy is it to install or use?

**IMAGE ROLE**
Installation / Ease-of-Use Image

AMAZON IMAGE RULES
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, text overlays, and icons.
3. Graphics must represent real product features only.
4. Do not show accessories not included with the product.
5. Maintain professional visual quality.

IMAGE FORMAT
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

STYLE CONSISTENCY
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

WORKFLOW MODE
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

OUTPUT FORMAT (JSON)

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 6,
   "image_type": "Ease of Use / Installation Image",
   "buyer_question": "How easy is it to install or use?",
   "layout_description": "",
   "headline_text": "",
   "supporting_text": "",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 22
```
**TASK:** Image 6 Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_style_lock
- image_strategy

**OBJECTIVE**
Generate Image 6 for the Amazon listing using the prepared image strategy.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 6 → How easy is it to install/use?

**IMAGE ROLE**
Installation / Ease-of-Use Image

**AMAZON IMAGE RULES**
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, icons, and text overlays.
3. Visual elements must represent real product features.
4. Do not depict accessories not included with the product.
5. Maintain professional image quality.

**IMAGE FORMAT**
Resolution: 1080 × 1920  
Aspect Ratio: 9:16  
Vertical composition

**STYLE CONSISTENCY**
Maintain the following parameters from workflow_state.json:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 6,
   "image_type": "Ease of Use / Installation Image",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 23
```
**TASK:** Image 7 Prompt Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock

**OBJECTIVE**
Generate the image-generation prompt for Image 7 of the Amazon listing.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 7 → What specifications or technical details matter?

**IMAGE ROLE**
Specifications / Feature Overview Infographic

AMAZON IMAGE RULES
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, text overlays, and icons.
3. Graphics must represent real product features only.
4. Do not show accessories not included with the product.
5. Maintain professional visual quality.

IMAGE FORMAT
- Resolution: 1080 × 1920
- Aspect Ratio: 9:16
- Vertical composition

STYLE CONSISTENCY
Use image_style_lock from workflow_state.json to maintain:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

WORKFLOW MODE
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

OUTPUT FORMAT (JSON)

{
 "reference_tag": "",
 "image_strategy": {
   "image_number": 7,
   "image_type": "Specifications Infographic",
   "buyer_question": "What specifications matter?",
   "layout_description": "",
   "headline_text": "",
   "supporting_text": "",
   "visual_design_direction": "",
   "image_generation_prompt": ""
 }
}
```

---
# PROMPT 24
```
**TASK:** Image 7 Generation

**INPUT**
Use the structured dataset contained in workflow_state.json.
reference_tag must be read from workflow_state.json and preserved unchanged.

The dataset includes:
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_style_lock
- image_strategy

**OBJECTIVE**
Generate Image 7 for the Amazon listing using the prepared image strategy.

**RULES**
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.

**BUYER QUESTION THIS IMAGE MUST ANSWER**
Image 7 → What specifications or technical details matter?

**IMAGE ROLE**
Specifications / Feature Overview Infographic

**AMAZON IMAGE RULES**
1. Product must be clearly visible and accurately represented.
2. Secondary images may include infographics, icons, and text overlays.
3. Visual elements must represent real product features.
4. Do not depict accessories not included with the product.
5. Maintain professional image quality.

**IMAGE FORMAT**
Resolution: 1080 × 1920  
Aspect Ratio: 9:16  
Vertical composition

**STYLE CONSISTENCY**
Maintain the following parameters from workflow_state.json:
- lighting
- camera lens style
- shadow behavior
- color profile
- product scale

**WORKFLOW MODE**
You are executing one step of an automated pipeline.
Only perform the requested task.
Do not summarize the workflow.
Do not suggest additional steps.

**OUTPUT FORMAT (JSON)**

{
 "reference_tag": "",
 "generated_image": {
   "image_number": 7,
   "image_type": "Specifications Infographic",
   "image_generation_prompt": ""
 }
}
```

---
