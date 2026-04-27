ImageGenerationToolSet
======================

The ImageGenerationToolSet provides image generation capabilities supporting both text-only models (DALL-E, Imagen) and multimodal models (Gemini Flash Image).

Overview
--------

Key features:

* **Text-to-Image**: Generate images from text descriptions
* **Style Transfer**: Use reference images for style guidance
* **Multiple Models**: Supports DALL-E, Imagen, and Gemini multimodal models
* **Automatic Storage**: Generated images are automatically saved and managed

Basic Usage
-----------

.. code-block:: python

   from pantheon.agent import Agent
   from pantheon.toolsets import ImageGenerationToolSet

   # Create image generation toolset
   image_tools = ImageGenerationToolSet(
       name="image_gen",
       fallback_vision_model="gemini/gemini-2.0-flash"
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="artist",
       instructions="You can generate images based on descriptions."
   )
   await agent.toolset(image_tools)

   await agent.chat()

Constructor Parameters
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Parameter
     - Type
     - Description
   * - ``name``
     - str
     - Name of the toolset (default: "image_generation")
   * - ``fallback_vision_model``
     - str | None
     - Model for describing reference images when using text-only generators. Default: "gemini/gemini-2.0-flash"

Tools Reference
---------------

generate_image
~~~~~~~~~~~~~~

Generate an image from a text description.

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="A serene mountain lake at sunset with snow-capped peaks",
       reference_images=None,
       model=None,  # Uses default model
       model_args=None
   )

**Parameters:**

- ``prompt``: Detailed image instruction. Include the subject, setting/context, composition/layout, visual style, colors/materials, lighting, camera/viewpoint, aspect-ratio intent, and any required or forbidden text. For diagrams or scientific figures, specify panels, labels, arrows, relative placement, and visual hierarchy. For edits or reference images, state what to preserve and what to change. Avoid vague prompts like "make it better"; describe the exact desired result.
- ``reference_images``: Optional list of file paths to use as style reference
- ``model``: Optional model override. Leave empty to use default. This can be a concrete model name, a ``provider/model-name`` identifier, or one of the built-in shortcuts ``"gemini"`` and ``"openai"``.
- ``model_args``: Optional provider-specific image generation arguments. Keep this simple: use only common controls unless the model requires otherwise. OpenAI-compatible image endpoints support ``size`` (default ``"1024x1024"`` in this tool), ``quality``, ``output_format``, and ``background``. Gemini supports ``aspect_ratio`` and ``image_size``; omitted Gemini values use the provider/model defaults.

**Returns:**

.. code-block:: python

   {
       "success": True,
       "images": ["/path/to/generated_image.png"],
       "model_used": "gemini/gemini-2.5-flash-image-preview"
   }

Using Reference Images
~~~~~~~~~~~~~~~~~~~~~~

For multimodal models (Gemini), you can provide reference images:

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="Combine the style of the first image with the subject of the second image",
       reference_images=[
           "/path/to/style_reference.png",
           "/path/to/subject_reference.png"
       ]
   )

For text-only models (DALL-E), reference images are described by a vision model and included in the prompt.

Supported Models
----------------

**Multimodal Models** (support image input + output):

- ``gemini/gemini-3-pro-image-preview``
- ``gemini/gemini-2.5-flash-image-preview``
- ``gemini/gemini-2.0-flash-exp-image-generation``

**Text-Only Models** (text-to-image only):

- ``dall-e-3``
- ``dall-e-2``
- Any model supported by the provider adapter's ``aimage_generation`` API

Model Selection
---------------

The default model is determined by Pantheon's settings:

.. code-block:: python

   # In settings.json
   {
       "image_gen_model": "gemini"  # or "openai", "high", "normal", "low", or a specific model name
   }

Or override per-call:

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="A futuristic cityscape",
       model="dall-e-3"
   )

Use a provider shortcut when you want the tool to select that provider's
default image model:

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="A publication-style cellular pathway diagram",
       model="gemini",
       model_args={"aspect_ratio": "16:9", "image_size": "2K"}
   )

For providers beyond the built-in shortcuts, pass a concrete model identifier.
OpenAI-compatible image endpoints are attempted through their configured
``base_url`` and API key:

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="A concise scientific icon set",
       model="openrouter/provider-image-model",
       model_args={"size": "1024x1024"}
   )

Examples
--------

Basic Image Generation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="""
       A cozy coffee shop interior with warm lighting,
       exposed brick walls, vintage furniture, and plants.
       Style: watercolor painting with soft edges.
       """
   )
   print(f"Generated: {result['images'][0]}")

Style Transfer with Multimodal Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use a reference image for style
   result = await image_tools.generate_image(
       prompt="Create a portrait in the style of the reference image, "
              "showing a woman reading a book by a window",
       reference_images=["/path/to/van_gogh_style.png"]
   )

Agent-Driven Image Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.agent import Agent
   from pantheon.toolsets import ImageGenerationToolSet, FileManagerToolSet

   image_tools = ImageGenerationToolSet(name="images")
   file_tools = FileManagerToolSet(name="files")

   artist = Agent(
       name="artist",
       instructions="""You are a creative artist assistant.
       When asked to create images:
       1. Generate detailed prompts based on user requests
       2. Use generate_image to create the artwork
       3. Save and describe the results"""
   )
   await artist.toolset(image_tools)
   await artist.toolset(file_tools)

   result = await artist.run(
       "Create a series of 3 images showing the four seasons in a Japanese garden"
   )

Best Practices
--------------

1. **Be specific in prompts**: Include details about style, colors, composition, lighting
2. **Use reference images**: For consistent style across multiple generations
3. **Choose appropriate models**: Multimodal for style transfer, DALL-E for text-only
4. **Check model capabilities**: Some models have size/quality limitations
5. **Handle failures gracefully**: Check ``success`` field in response

Error Handling
--------------

.. code-block:: python

   result = await image_tools.generate_image(
       prompt="A beautiful landscape"
   )

   if result["success"]:
       print(f"Image saved to: {result['images'][0]}")
   else:
       print(f"Error: {result['error']}")
