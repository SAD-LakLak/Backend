from django.test import TestCase
from django.urls import reverse
from core.models import *

# Create your tests here.
# class PackageModelTests(TestCase):
#     def test_package_price(self):
#         # Set a test provider, two products and a package containing those two
#         provider = CustomUser.objects.create(
#             role="supplier",
#         )
#         product1 = Product.objects.create(
#             provider=provider,
#             name="prod1",
#             type="food",
#             price=5,
#             stock=10,
#         )
#         product2 = Product.objects.create(
#             provider=provider,
#             name="prod2",
#             type="clothing",
#             price=3,
#             stock=1,
#         )
#         package = Package.objects.create(
#             name="package",
#         )

#         package.products.add(product1)
#         package.products.add(product2)

#         # The package price should be the sum of the price of the two products
#         self.assertEqual(package.total_price, 5 + 3)

#         # If one of products' price changes, the package's price should update too
#         product1.price = 60
#         product1.save()
#         self.assertEqual(package.total_price, 60 + 3)



class UserTests(TestCase):
    def test_user_registration(self):
        response = self.client.post(
            reverse("core:register"),
                {
                    "username": "ali",
                    "email": "ali@laklakbox.ir",
                    "password": "12345678",
                    "role": "customer"
                }
        )
        self.assertGreaterEqual(response.status_code, 200)
        self.assertLess(response.status_code, 300)
        ali_users = CustomUser.objects.filter(username="ali")
        self.assertEqual(len(ali_users), 1)
        new_user = ali_users[0]
        self.assertEqual(new_user.role, "customer")
    
