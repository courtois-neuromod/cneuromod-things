THINGS image annotations
========================

Image annotations for the THINGS image dataset, which comprises the current stimulus set, can be retrieved from the [THINGS Initiative](https://things-initiative.org/) website [here](https://osf.io/jum2f/).

To characterize stimulus content, we created 13 boolean flags that reflect whether an image contains faces or body parts (animal or human), and whether it features a complex scene, an enriched background or a lone object devoid of context. A manual annotator rated all 4k+ images in the CNeuroMod-things stimulus set with the 13 flags, which are defined below. Each image was annotated twice for consistency. Results are compiled in ``task-thing_desc-manual_annotation.tsv`` and columns are described in ``task-things_desc-manual_annotation.json``.

**face** \
Contains any face, whole or partial (e.g., eyes or smile), central or in the periphery (incidental to the image’s main focus). Faces can be human or not, real or artificial (a doll’s face, a cartoon cat face, a face reflected in a soap bubble).

**body** \
Contains any body (which may include a face) or non-face body part(s), central or in the periphery. Bodies can be human or not, real or artificial (a robot’s body, an octopus tentacle, an artificial limb), clothed or not (e.g., a person’s legs in an image featuring pants, a gloved hand holding a wine glass, a head with visible shoulders and torso).

**human face** \
Contains any face or portion of a face with human features, central or in the periphery, real or artificial (a doll’s face, a cartoon of a person’s face, etc).

**human body** \
Contains any human body or non-face human body part, central or in the periphery, real or artificial (a drawn hand).

**non-human mammal face** \
Contains any face with non-human mammalian features, central or in the periphery, real or artificial (a cartoon dog face). Includes: faces of rodents, dogs, felines, cows, deers, etc. Excludes: faces of insects, reptiles, fish, birds, sea mammals* (e.g., dolphins and whales).

**non-human mammal body** \
Contains any body or non-face body part from a non-human mammal, central or in the periphery, real or artificial (a robot dog leg).
Includes: rodents, felines, cows, deers, etc.
Excludes: insects, reptiles, fish, birds, sea mammals* (e.g., dolphins and whales).

**central face** \
Contains a face or a portion of a face (human or not, real or artificial) within the image’s central focus. E.g., An image featuring a person jumping on a pogo stick is considered central if the face is visible, while faces of random spectators in the background are not. Although the face does not need to be in the middle of the image to be “central” per se, the face should be visible when gazing at a central fixation cross, and it must be part of the image’s main focus of interest.

**central body** \
Contains a body or non-face body part within the image’s central focus. E.g., an image featuring a hand holding an item of interest is central, while a silhouette visible next to an aircraft carrier seen from afar is not. Although the body (part) does not need to be in the center of the image to be “central”, it should be visible when gazing at a central fixation cross, and it must be part of the image’s main focus of interest.

**artificial face** \
Contains any representation of a human, animal or humanoid face that is not a real (living) face. Eg., a doll face or mannequin head, a cartoon bird face, a robot with facial features like eyes and a smile, an action figure, a painting or a photo of a face on a banner.

**artificial body** \
Contains any representation of a human, animal or humanoid body or non-face body part that is not a real (living) body (part). Eg., a statue, a prosthetic leg, a robotic hand, a drawing of a bird on a teapot.

**scene** \
An item pictured in an environment with a background and a foreground that gives the sense of a place around it. A scene includes scenery, a view point and some perspective. It can be the image of a large object in a specific setting, like an aircraft in a hangard, a sofa in the middle of a living room, an anchor by a waterfront, an elephant at the zoo or a person skateboarding in a busy park.

**rich background** \
An image of an object taken from closer than a scene, but that still includes items, people or animals clearly visible in the background. E.g., a backpack on someone’s back walking away toward some trees, a tool in a garage with equipment visible behind it, a plant in a garden surrounded by other plants, a beer glass held by a person sitting between others, an apple on a table with orchard trees behind it.

**lone object** \
The featured object is shown centrally with no additional objects visible in the periphery or background. Not only is the object shown by itself, but the empty background is uniform and minimally textured (no carpet, dinner mat or wooden fence behind) or blurred so that only the lone object is in focus. Note that objects can either be shown with zero background (the “lone objects” flag), with minimal background (e.g., an apple in a basket on a table), with noticeable background (the “rich background” flag) or within a scene (with background and perspective).

*Although they are obviously mammals, sea mammal’s features are very different from humans, hence this categorical choice.
