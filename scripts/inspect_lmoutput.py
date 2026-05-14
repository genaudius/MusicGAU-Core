from audiocraft.models.lm import LMOutput
import dataclasses
print("LMOutput fields:", [f.name for f in dataclasses.fields(LMOutput)])
print("Doc:", LMOutput.__doc__)
