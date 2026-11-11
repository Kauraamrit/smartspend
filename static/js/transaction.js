document.addEventListener("DOMContentLoaded", function () {

    const transactions = document.querySelectorAll(".transaction-row");

    transactions.forEach(function (transaction) {

        transaction.addEventListener("click", function () {

            // Remove selection from all transactions
            transactions.forEach(function (item) {
                item.classList.remove("selected");
            });

            // Select the clicked transaction
            transaction.classList.add("selected");

        });

    });

});