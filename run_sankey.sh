#!/bin/bash

# Sankey Charts Launcher Script
# Run different Sankey visualization pages

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Global Liquidity Dashboard - Sankey Charts        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Menu
echo -e "${GREEN}Select Sankey Chart to Launch:${NC}"
echo ""
echo "  1) Income Statement Sankey (Revenue → Net Income)"
echo "  2) Fund Holdings Sankey (Fund → Stocks, Stock → Funds)"
echo "  3) Macro Liquidity Sankey (Liquidity → Assets)"
echo "  4) Run All Tests"
echo "  5) Exit"
echo ""

read -p "Enter your choice [1-5]: " choice

case $choice in
    1)
        echo -e "${YELLOW}Launching Income Statement Sankey...${NC}"
        streamlit run dashboard/pages/sankey_income.py
        ;;
    2)
        echo -e "${YELLOW}Launching Fund Holdings Sankey...${NC}"
        streamlit run dashboard/pages/sankey_funds.py
        ;;
    3)
        echo -e "${YELLOW}Launching Macro Liquidity Sankey...${NC}"
        streamlit run dashboard/pages/sankey_macro.py
        ;;
    4)
        echo -e "${YELLOW}Running Sankey Module Tests...${NC}"
        pytest tests/test_sankey_transform.py tests/test_fund_holdings_sankey.py -v --tb=short
        ;;
    5)
        echo -e "${GREEN}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Exiting...${NC}"
        exit 1
        ;;
esac
