# SocialMapper v0.5.2 Release Notes

## 🔧 Breaking Changes & Upgrades

### Pydantic v2 Migration Complete

SocialMapper has been fully upgraded to Pydantic v2, bringing improved performance and modern validation patterns.

**What was upgraded:**
- All `@validator` decorators migrated to `@field_validator` with `@classmethod`
- Updated coordinate validation models in `socialmapper.util.coordinate_validation`
- Maintained full backward compatibility for end users

**Technical Details:**
- `CoordinatePoint`, `POICoordinate`, and `CoordinateCluster` models now use Pydantic v2 syntax
- All field validators properly migrated and tested
- No API changes for end users - models work exactly the same
- Enhanced validation performance from Pydantic v2's Rust-based core

**Files Modified:**
- `socialmapper/util/coordinate_validation.py` - Validator syntax updated
- Version bumped to 0.5.2

## 🧪 Testing

All coordinate validation models have been thoroughly tested and verified to work correctly with the new Pydantic v2 syntax.

## 📚 Developer Notes

If you're extending SocialMapper with custom Pydantic models, please use the new v2 syntax:

```python
# New Pydantic v2 syntax
from pydantic import BaseModel, field_validator

class MyModel(BaseModel):
    my_field: str
    
    @field_validator('my_field')
    @classmethod
    def validate_my_field(cls, v):
        # validation logic
        return v
```

## 🔗 Dependencies

- Pydantic: `>=2.0.0` (already required in previous versions)
- All other dependencies remain unchanged

---

**Full Changelog:** v0.5.1...v0.5.2 