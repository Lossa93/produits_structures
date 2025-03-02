from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import holidays
#-------------------------------------------------------------------------------------------------------
#----------------------------Script pour implémenter les classes utilitaires----------------------------
#-------------------------------------------------------------------------------------------------------

#Classe maturité
class Maturity_handler:
    def __init__(self, convention: str, format_date: str, rolling_convention: str, market: str) -> None:
        self.__convention = convention
        self.__format_date = format_date
        self.__rolling_convention = rolling_convention
        self.__market = market
        self.__calendar = self.__get_market_calendar(dt.today()-timedelta(days=100*360), dt.today()+timedelta(days=100*360))
        pass

    def __convention_handler(self, valuation_date, end_date) -> float:
        """Returns the corresponding year_fraction (end_date - valuation_date)
            corresponding to the convention of the handler."""
        d1, m1, y1 = valuation_date.day, valuation_date.month, valuation_date.year
        d2, m2, y2 = end_date.day, end_date.month, end_date.year
        if d1 == 31:
            d1 = 30
        if d2 == 31:
            d2 = 30
        if self.__convention == "30/360":
            return (360*(y2 - y1) + 30 * (m2 - m1) + (d2 - d1))/360
        elif self.__convention == "Act/360":
            delta_days  = (end_date - valuation_date).days
            return delta_days/360
        elif self.__convention == "Act/365":
            delta_days  = (end_date - valuation_date).days
            return delta_days/365
        elif self.__convention == "Act/Act":
            days_count = 0
            current_date = valuation_date
            while current_date < end_date:
                year_end = dt(current_date.year, 12, 31)
                if year_end > end_date:
                    year_end = end_date
                days_in_year = (dt(current_date.year, 12, 31) - dt(current_date.year, 1, 1)).days + 1
                days_count += (year_end - current_date).days / days_in_year
                current_date = year_end + timedelta(days=1)
            return days_count
        else:
            raise ValueError(f"Entered Convention: {self.__convention} is not handled ! (30/360, Act/360, Act/365, Act/Act)")

    def __get_market_calendar(self, start_date, end_date):
        try:
            return holidays.financial_holidays(market=self.__market, years=(range(start_date.year, end_date.year)))
        except:
            raise ValueError(f"Error calendar: {self.__market} is not supported Choose (XECB, IFEU, XNYS, BVMF)")
        pass
        
    def __get_next_day(self, date):
        while date.weekday() >= 5 or date in self.__calendar:
            date += timedelta(days=1)
        return date
    
    def __get_previous_day(self, date):
        while date.weekday() >= 5 or date in self.__calendar:
            date -= timedelta(days=1)
        return date

    def __apply_rolling_convention(self, date):
        if self.__rolling_convention == "Following":
            return self.__get_next_day(date)
        
        elif self.__rolling_convention == "Modified Following":
            new_date = self.__get_next_day(date)
            if new_date.month != date.month:
                return self.__get_previous_day(date)
            else:
                return new_date
            
        elif self.__rolling_convention == "Preceding":
            return self.__get_previous_day(date)
        
        elif self.__rolling_convention == "Modified Preceding":
            new_date = self.__get_previous_day(date)
            print(new_date)
            if new_date.month != date.month:
                return self.__get_next_day(date)
            else:
                return new_date
        else:
            raise ValueError(f"Rolling Convention {self.__rolling_convention} is not supported ! Choose: Following, Modified Following, Preceding, Modified Preceding")

    def get_year_fraction(self, valuation_date, end_date) -> float:
        """Takes valuatio_date and end_date as strings, convert to datetime and 
            get year_fraction (float) depending on the self.__convention"""
        #If dates arrives in the strings
        if type(valuation_date) == str:
            valuation_date = dt.strptime(valuation_date, self.__format_date)
        if type(end_date) == str:
            end_date = dt.strptime(end_date, self.__format_date)

        #We need to get the real "openned days" of the market (calendars) = Modified Following, etc.    
        if valuation_date.weekday()>=5 or valuation_date in self.__calendar:
            valuation_date = self.__apply_rolling_convention(valuation_date)
        if valuation_date.weekday()>=5 or valuation_date in self.__calendar:
            end_date = self.__apply_rolling_convention(end_date)
        return self.__convention_handler(valuation_date, end_date)

class PaymentScheduleHandler:
    def __init__(self, valutation_date: str, end_date:str, periodicity: str) -> None:
        self.__valuation_date = valutation_date
        self.__end_date = end_date
        self.__periodicity = periodicity
        pass

    def build_schedule(self, format_date: str, convention: str, rolling_convention: str, market: str) -> tuple:
        """Takes a start_date, end_date, periodicity :: returns a tuple of year_fractions
            tuple because read only."""
        self.__valuation_date = dt.strptime(self.__valuation_date, format_date)
        self.__end_date = dt.strptime(self.__end_date, format_date)
        list_dates = self.__get_intermediary_dates()

        maturityhandler = Maturity_handler(convention, format_date, rolling_convention, market)

        list_year_fractions = []
        for date in list_dates[1:]:
            list_year_fractions.append(maturityhandler.get_year_fraction(list_dates[1], date))

        return tuple(list_year_fractions)

    def __get_intermediary_dates(self) -> list:
        """Build a dates list with all intermediary dates between start and end based on periodicity."""
        """Supported periodicity: monthly, quaterly, semi-annually, annually."""
        list_dates = [self.__valuation_date]
        count_date = self.__valuation_date
        while count_date < self.__end_date:
            if self.__periodicity == "monthly":
                count_date += relativedelta(months=1)
                list_dates.append(count_date)
            elif self.__periodicity == "quaterly":
                count_date += relativedelta(months=3)
                list_dates.append(count_date)
            elif self.__periodicity == "semi-annually":
                count_date += relativedelta(months=6)
                list_dates.append(count_date)
            elif self.__periodicity == "annually":
                count_date += relativedelta(years=1)
                list_dates.append(count_date)
            else:
                raise ValueError(f"Entered periodicity {self.__periodicity} is not supported. Supported periodicity: monthly, quaterly, semi-annually, annually.")
        
        list_dates.append(self.__end_date)
        return list_dates
        
    

#Classe de rate et courbe de taux

#Classe de vol
