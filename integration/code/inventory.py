"""
Inventory Module - Tracks cars, spare parts, tools, and cash balance.

Responsibilities:
- Add/remove cars from inventory
- Track car status (available, in_race, damaged, in_repair)
- Manage spare parts inventory
- Track tools
- Manage cash balance
"""

from typing import Dict, List, Optional

try:
    from .models import Car, CarStatus, SparePart, Tool, generate_id
    from .exceptions import (
        CarNotFoundError,
        CarNotAvailableError,
        InsufficientFundsError,
        InsufficientPartsError,
        InvalidCarDataError
    )
except ImportError:
    from models import Car, CarStatus, SparePart, Tool, generate_id
    from exceptions import (
        CarNotFoundError,
        CarNotAvailableError,
        InsufficientFundsError,
        InsufficientPartsError,
        InvalidCarDataError
    )


class InventoryModule:
    """
    Manages the crew's inventory: cars, spare parts, tools, and cash.

    This module is central to the system as:
    - Race Management uses it to get available cars
    - Results module updates cash balance after races
    - Mission Planning uses it for repair missions
    """

    LOW_CASH_THRESHOLD = 500.0
    LOW_PARTS_THRESHOLD = 2

    def __init__(self, initial_cash: float = 0.0):
        """
        Initialize inventory with optional starting cash.

        Args:
            initial_cash: Starting cash balance.
        """
        self._cars: Dict[str, Car] = {}
        self._spare_parts: Dict[str, SparePart] = {}
        self._tools: Dict[str, Tool] = {}
        self._cash_balance: float = max(0.0, initial_cash)
        self._low_inventory_callback = None

    def set_low_inventory_callback(self, callback):
        """Set a callback function for low inventory alerts."""
        self._low_inventory_callback = callback

    # =================== CAR MANAGEMENT ===================

    def add_car(
        self,
        make: str,
        model: str,
        year: int,
        car_id: Optional[str] = None,
        performance_rating: int = 5
    ) -> Car:
        """
        Add a new car to inventory.

        Args:
            make: Car manufacturer.
            model: Car model name.
            year: Manufacturing year.
            car_id: Optional custom ID.
            performance_rating: Performance rating (1-10).

        Returns:
            The newly created Car object.

        Raises:
            InvalidCarDataError: If car data is invalid.
        """
        # Validate inputs
        if not make or not isinstance(make, str):
            raise InvalidCarDataError("Make must be a non-empty string")
        if not model or not isinstance(model, str):
            raise InvalidCarDataError("Model must be a non-empty string")
        if not isinstance(year, int) or year < 1900 or year > 2100:
            raise InvalidCarDataError("Year must be a valid integer between 1900 and 2100")
        if not isinstance(performance_rating, int) or performance_rating < 1 or performance_rating > 10:
            raise InvalidCarDataError("Performance rating must be between 1 and 10")

        # Generate ID if not provided
        if car_id is None:
            car_id = generate_id()

        car = Car(
            car_id=car_id,
            make=make.strip(),
            model=model.strip(),
            year=year,
            performance_rating=performance_rating,
            status=CarStatus.AVAILABLE
        )

        self._cars[car_id] = car
        return car

    def get_car(self, car_id: str) -> Car:
        """
        Retrieve a car by ID.

        Args:
            car_id: The unique identifier of the car.

        Returns:
            The Car object.

        Raises:
            CarNotFoundError: If car doesn't exist.
        """
        if car_id not in self._cars:
            raise CarNotFoundError(car_id)
        return self._cars[car_id]

    def list_all_cars(self) -> List[Car]:
        """
        Get all cars in inventory.

        Returns:
            List of all Car objects.
        """
        return list(self._cars.values())

    def list_available_cars(self) -> List[Car]:
        """
        Get all cars that are available for use.

        Returns:
            List of available Car objects.
        """
        return [c for c in self._cars.values() if c.status == CarStatus.AVAILABLE]

    def list_damaged_cars(self) -> List[Car]:
        """
        Get all damaged cars.

        Returns:
            List of damaged Car objects.
        """
        return [c for c in self._cars.values() if c.status == CarStatus.DAMAGED]

    def update_car_status(self, car_id: str, status: str) -> Car:
        """
        Update a car's status.

        Args:
            car_id: The unique identifier of the car.
            status: The new status (available, in_race, damaged, in_repair).

        Returns:
            The updated Car object.

        Raises:
            CarNotFoundError: If car doesn't exist.
            InvalidCarDataError: If status is invalid.
        """
        if car_id not in self._cars:
            raise CarNotFoundError(car_id)

        try:
            status_enum = CarStatus(status.lower().strip())
        except ValueError:
            raise InvalidCarDataError(
                f"Invalid status: '{status}'. Valid statuses: available, in_race, damaged, in_repair"
            )

        self._cars[car_id].status = status_enum
        return self._cars[car_id]

    def is_car_available(self, car_id: str) -> bool:
        """
        Check if a car is available.

        Args:
            car_id: The unique identifier of the car.

        Returns:
            True if car is available.

        Raises:
            CarNotFoundError: If car doesn't exist.
        """
        if car_id not in self._cars:
            raise CarNotFoundError(car_id)
        return self._cars[car_id].status == CarStatus.AVAILABLE

    def set_car_damage_level(self, car_id: str, damage_level: int) -> Car:
        """
        Set a car's damage level.

        Args:
            car_id: The unique identifier of the car.
            damage_level: The damage level (0-100).

        Returns:
            The updated Car object.

        Raises:
            CarNotFoundError: If car doesn't exist.
            InvalidCarDataError: If damage level is invalid.
        """
        if car_id not in self._cars:
            raise CarNotFoundError(car_id)

        if not isinstance(damage_level, int) or damage_level < 0 or damage_level > 100:
            raise InvalidCarDataError("Damage level must be between 0 and 100")

        self._cars[car_id].damage_level = damage_level

        # Auto-update status if heavily damaged
        if damage_level > 50:
            self._cars[car_id].status = CarStatus.DAMAGED

        return self._cars[car_id]

    def remove_car(self, car_id: str) -> bool:
        """
        Remove a car from inventory.

        Args:
            car_id: The unique identifier of the car.

        Returns:
            True if successfully removed.

        Raises:
            CarNotFoundError: If car doesn't exist.
        """
        if car_id not in self._cars:
            raise CarNotFoundError(car_id)

        del self._cars[car_id]
        return True

    # =================== SPARE PARTS MANAGEMENT ===================

    def add_spare_parts(self, part_name: str, quantity: int, unit_cost: float = 0.0) -> SparePart:
        """
        Add spare parts to inventory.

        Args:
            part_name: Name of the part.
            quantity: Number of parts to add.
            unit_cost: Cost per unit.

        Returns:
            The updated SparePart object.

        Raises:
            ValueError: If inputs are invalid.
        """
        if not part_name or not isinstance(part_name, str):
            raise ValueError("Part name must be a non-empty string")
        if not isinstance(quantity, int) or quantity < 1:
            raise ValueError("Quantity must be a positive integer")

        part_name = part_name.lower().strip()

        if part_name in self._spare_parts:
            self._spare_parts[part_name].quantity += quantity
        else:
            self._spare_parts[part_name] = SparePart(
                name=part_name,
                quantity=quantity,
                unit_cost=max(0.0, unit_cost)
            )

        return self._spare_parts[part_name]

    def use_spare_parts(self, part_name: str, quantity: int) -> SparePart:
        """
        Use spare parts from inventory.

        Args:
            part_name: Name of the part.
            quantity: Number of parts to use.

        Returns:
            The updated SparePart object.

        Raises:
            InsufficientPartsError: If not enough parts available.
        """
        if not part_name or not isinstance(part_name, str):
            raise ValueError("Part name must be a non-empty string")

        part_name = part_name.lower().strip()

        if part_name not in self._spare_parts:
            raise InsufficientPartsError(part_name, quantity, 0)

        available = self._spare_parts[part_name].quantity
        if available < quantity:
            raise InsufficientPartsError(part_name, quantity, available)

        self._spare_parts[part_name].quantity -= quantity

        # Check for low inventory and trigger callback
        if (self._spare_parts[part_name].quantity <= self.LOW_PARTS_THRESHOLD
                and self._low_inventory_callback):
            self._low_inventory_callback("parts", part_name)

        return self._spare_parts[part_name]

    def get_spare_parts_quantity(self, part_name: str) -> int:
        """
        Get the quantity of a specific spare part.

        Args:
            part_name: Name of the part.

        Returns:
            Quantity available.
        """
        part_name = part_name.lower().strip()
        if part_name not in self._spare_parts:
            return 0
        return self._spare_parts[part_name].quantity

    def list_all_spare_parts(self) -> List[SparePart]:
        """
        Get all spare parts in inventory.

        Returns:
            List of all SparePart objects.
        """
        return list(self._spare_parts.values())

    def list_low_spare_parts(self) -> List[SparePart]:
        """
        Get all spare parts that are low on stock.

        Returns:
            List of low-stock SparePart objects.
        """
        return [p for p in self._spare_parts.values() if p.quantity <= self.LOW_PARTS_THRESHOLD]

    # =================== TOOLS MANAGEMENT ===================

    def add_tools(self, tool_name: str, quantity: int, condition: str = "good") -> Tool:
        """
        Add tools to inventory.

        Args:
            tool_name: Name of the tool.
            quantity: Number of tools to add.
            condition: Condition of the tools.

        Returns:
            The updated Tool object.
        """
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not isinstance(quantity, int) or quantity < 1:
            raise ValueError("Quantity must be a positive integer")

        tool_name = tool_name.lower().strip()

        if tool_name in self._tools:
            self._tools[tool_name].quantity += quantity
        else:
            self._tools[tool_name] = Tool(
                name=tool_name,
                quantity=quantity,
                condition=condition
            )

        return self._tools[tool_name]

    def list_all_tools(self) -> List[Tool]:
        """
        Get all tools in inventory.

        Returns:
            List of all Tool objects.
        """
        return list(self._tools.values())

    # =================== CASH MANAGEMENT ===================

    def get_cash_balance(self) -> float:
        """
        Get the current cash balance.

        Returns:
            Current cash balance.
        """
        return self._cash_balance

    def update_cash_balance(self, amount: float) -> float:
        """
        Update the cash balance (add or subtract).

        Args:
            amount: Amount to add (positive) or subtract (negative).

        Returns:
            New cash balance.

        Raises:
            InsufficientFundsError: If subtraction would result in negative balance.
        """
        new_balance = self._cash_balance + amount

        if new_balance < 0:
            raise InsufficientFundsError(abs(amount), self._cash_balance)

        self._cash_balance = new_balance

        # Check for low cash and trigger callback
        if new_balance <= self.LOW_CASH_THRESHOLD and self._low_inventory_callback:
            self._low_inventory_callback("cash", str(new_balance))

        return self._cash_balance

    def add_cash(self, amount: float) -> float:
        """
        Add cash to balance.

        Args:
            amount: Amount to add (must be positive).

        Returns:
            New cash balance.

        Raises:
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return self.update_cash_balance(amount)

    def deduct_cash(self, amount: float) -> float:
        """
        Deduct cash from balance.

        Args:
            amount: Amount to deduct (must be positive).

        Returns:
            New cash balance.

        Raises:
            InsufficientFundsError: If insufficient funds.
            ValueError: If amount is not positive.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return self.update_cash_balance(-amount)

    def is_low_on_cash(self) -> bool:
        """
        Check if cash balance is below threshold.

        Returns:
            True if cash is low.
        """
        return self._cash_balance <= self.LOW_CASH_THRESHOLD

    # =================== INVENTORY SUMMARY ===================

    def get_inventory_summary(self) -> dict:
        """
        Get a summary of the entire inventory.

        Returns:
            Dictionary with inventory statistics.
        """
        return {
            "total_cars": len(self._cars),
            "available_cars": len(self.list_available_cars()),
            "damaged_cars": len(self.list_damaged_cars()),
            "total_spare_parts_types": len(self._spare_parts),
            "total_tools_types": len(self._tools),
            "cash_balance": self._cash_balance,
            "is_low_on_cash": self.is_low_on_cash(),
            "low_stock_parts": [p.name for p in self.list_low_spare_parts()]
        }
