"""MoneyPoly module."""
class Property:
    """Represents a single purchasable property tile on the MoneyPoly board."""

    FULL_GROUP_MULTIPLIER = 2

    def __init__(self, name, position, financials, group=None):
        """Property class."""
        self.name = name
        self.position = position
        self.price = financials[0]
        self.base_rent = financials[1]
        self.mortgage_value = self.price // 2
        # Grouping state variables to reduce attribute count
        self.state = {"owner": None, "is_mortgaged": False, "houses": 0}
        self.group = group
        if group is not None and self not in group.properties:
            group.properties.append(self)

    def get_rent(self):
        """
        Return the rent owed for landing on this property.
        Rent is doubled if the owner holds the entire colour group.
        Returns 0 if the property is mortgaged.
        """
        if self.state["is_mortgaged"]:
            return 0
        if self.group is not None and self.group.all_owned_by(self.state["owner"]):
            return self.base_rent * self.FULL_GROUP_MULTIPLIER
        return self.base_rent

    def mortgage(self):
        """
        Mortgage this property and return the payout to the owner.
        Returns 0 if already mortgaged.
        """
        if self.state["is_mortgaged"]:
            return 0
        self.state["is_mortgaged"] = True
        return self.mortgage_value

    def unmortgage(self):
        """
        Lift the mortgage on this property.
        Returns the cost (110 % of mortgage value), or 0 if not mortgaged.
        """
        if not self.state["is_mortgaged"]:
            return 0
        cost = int(self.mortgage_value * 1.1)
        self.state["is_mortgaged"] = False
        return cost

    def is_available(self):
        """Return True if this property can be purchased (unowned, not mortgaged)."""
        return self.state["owner"] is None and not self.state["is_mortgaged"]

    def __repr__(self):
        owner_name = self.state["owner"].name if self.state["owner"] else "unowned"
        return f"Property({self.name!r}, pos={self.position}, owner={owner_name!r})"


class PropertyGroup:
    """PropertyGroup class."""
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.properties = []

    def add_property(self, prop):
        """Add a Property to this group and back-link it."""
        if prop not in self.properties:
            self.properties.append(prop)
            prop.group = self

    def all_owned_by(self, player):
        """Return True if every property in this group is owned by `player`."""
        if player is None:
            return False
        return all(p.state["owner"] == player for p in self.properties)

    def get_owner_counts(self):
        """Return a dict mapping each owner to how many properties they hold in this group."""
        counts = {}
        for prop in self.properties:
            if prop.state["owner"] is not None:
                counts[prop.state["owner"]] = counts.get(prop.state["owner"], 0) + 1
        return counts

    def size(self):
        """Return the number of properties in this group."""
        return len(self.properties)

    def __repr__(self):
        return f"PropertyGroup({self.name!r}, {len(self.properties)} properties)"
