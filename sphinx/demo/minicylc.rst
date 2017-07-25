MiniCylc Test
=============

Basic Example - Demo Colour Theme
---------------------------------

.. minicylc::
   :align: center
   :theme: demo

    a => b => c
    b => d => f
    e => f


Full Example With Code Snippet
------------------------------

.. minicylc::
   :snippet:

   a => b => c => d
   b => (e & f & g & h & i & j)
   e => t
   f => u
   (e & f & (g & h) & i & j) => k
   d => l & m => n
   k | n => o & p
   o & p => q & r => s


