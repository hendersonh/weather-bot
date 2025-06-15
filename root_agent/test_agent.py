import unittest
from unittest.mock import patch, Mock
import requests
import os
import datetime # Added for mocking datetime.now()
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # Added for timezone objects and exception
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError # Added geopy exceptions

from root_agent.agent import get_weather, get_current_time # Added get_current_time

class TestGetWeather(unittest.TestCase):

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_success(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "dummy_api_key"
      mock_response = Mock()
      mock_response.status_code = 200
      mock_response.json.return_value = {
          "cod": 200,
          "weather": [{"description": "clear sky"}],
          "main": {"temp": 25.5}
      }
      mock_requests_get.return_value = mock_response

      city = "TestCity"
      expected_report = f"The weather in {city} is clear sky with a temperature of 25.5°C."
      expected_result = {"status": "success", "report": expected_report}

      result = get_weather(city)
      
      self.assertEqual(result, expected_result)
      mock_getenv.assert_called_once_with("OPENWEATHER_API_KEY")
      mock_requests_get.assert_called_once_with(
          "http://api.openweathermap.org/data/2.5/weather",
          params={"q": city, "appid": "dummy_api_key", "units": "metric"},
          timeout=10
      )

  @patch('root_agent.agent.os.getenv')
  def test_get_weather_api_key_missing(self, mock_getenv):
      mock_getenv.return_value = None
      city = "TestCity"
      expected_result = {
          "status": "error",
          "report": "OpenWeather API key not found. Please set OPENWEATHER_API_KEY environment variable."
      }
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_getenv.assert_called_once_with("OPENWEATHER_API_KEY")

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_invalid_api_key(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "invalid_dummy_key"
      mock_response = Mock()
      mock_response.status_code = 401
      mock_response.json.return_value = {"cod": 401, "message": "Invalid API key."}
      mock_response.raise_for_status = Mock(side_effect=requests.exceptions.HTTPError(response=mock_response))
      mock_requests_get.return_value = mock_response
      
      city = "TestCity"
      expected_report = f"API Error for {city}: Invalid API key or unauthorized."
      expected_result = {"status": "error", "report": expected_report}
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_requests_get.assert_called_once()

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_city_not_found(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "dummy_api_key"
      mock_response = Mock()
      mock_response.status_code = 404
      mock_response.json.return_value = {"cod": "404", "message": "city not found"}
      mock_response.raise_for_status = Mock(side_effect=requests.exceptions.HTTPError(response=mock_response))
      mock_requests_get.return_value = mock_response
      
      city = "UnknownCity"
      expected_report = f"API Error for {city}: City not found by API endpoint or resource not found."
      expected_result = {"status": "error", "report": expected_report}
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_requests_get.assert_called_once()

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_connection_error(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "dummy_api_key"
      mock_requests_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
      
      city = "TestCity"
      expected_report = f"Connection error for {city}: Failed to connect"
      expected_result = {"status": "error", "report": expected_report}
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_requests_get.assert_called_once()

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_timeout_error(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "dummy_api_key"
      mock_requests_get.side_effect = requests.exceptions.Timeout("Request timed out")
      
      city = "TestCity"
      expected_report = f"Request timed out for {city}: Request timed out"
      expected_result = {"status": "error", "report": expected_report}
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_requests_get.assert_called_once()

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_generic_request_exception(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "dummy_api_key"
      mock_requests_get.side_effect = requests.exceptions.RequestException("Some generic request error")
      
      city = "TestCity"
      expected_report = f"Error fetching weather for {city}: Some generic request error"
      expected_result = {"status": "error", "report": expected_report}
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_requests_get.assert_called_once()

  @patch('root_agent.agent.requests.get')
  @patch('root_agent.agent.os.getenv')
  def test_get_weather_malformed_json_response(self, mock_getenv, mock_requests_get):
      mock_getenv.return_value = "dummy_api_key"
      mock_response = Mock()
      mock_response.status_code = 200
      mock_response.json.return_value = {
          "cod": 200,
          "coord": {"lon": -0.1257, "lat": 51.5085}
      }
      mock_requests_get.return_value = mock_response
      
      city = "TestCity"
      expected_report = f"The weather in {city} is not available with a temperature of not available°C."
      expected_result = {"status": "success", "report": expected_report}
      result = get_weather(city)
      self.assertEqual(result, expected_result)
      mock_requests_get.assert_called_once()

  # --- Tests for get_current_time (Nominatim & TimezoneFinder) ---

  @patch('root_agent.agent.datetime')
  @patch('root_agent.agent.tf') # Patch the 'tf' object directly
  @patch('root_agent.agent.geolocator.geocode')
  def test_get_current_time_success_nominatim(self, mock_geocode, mock_tf_object, mock_datetime):
      mock_location = Mock()
      mock_location.latitude = 43.6532
      mock_location.longitude = -79.3832
      mock_geocode.return_value = mock_location

      mock_tf_object.timezone_at.return_value = "America/Toronto"

      fixed_now = datetime.datetime(2025, 6, 15, 10, 30, 0, tzinfo=ZoneInfo("America/Toronto"))
      mock_datetime_instance = mock_datetime.datetime
      mock_datetime_instance.now.return_value = fixed_now
      
      city = "Toronto"
      expected_timezone_str = "America/Toronto"
      expected_report_time_part = fixed_now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
      expected_report = f"The current time in {city} ({expected_timezone_str}) is {expected_report_time_part}"
      expected_result = {"status": "success", "report": expected_report}

      result = get_current_time(city)

      self.assertEqual(result, expected_result)
      mock_geocode.assert_called_once_with(city, timeout=10)
      mock_tf_object.timezone_at.assert_called_once_with(lng=-79.3832, lat=43.6532)
      mock_datetime_instance.now.assert_called_once_with(ZoneInfo("America/Toronto"))

  @patch('root_agent.agent.geolocator.geocode')
  def test_get_current_time_city_not_geocoded_nominatim(self, mock_geocode):
      mock_geocode.return_value = None
      
      city = "UnknownCity"
      expected_report = f"City '{city}' not found or could not be geocoded."
      expected_result = {"status": "error", "report": expected_report}

      result = get_current_time(city)

      self.assertEqual(result, expected_result)
      mock_geocode.assert_called_once_with(city, timeout=10)

  @patch('root_agent.agent.geolocator.geocode')
  def test_get_current_time_geocoding_timeout_nominatim(self, mock_geocode):
      mock_geocode.side_effect = GeocoderTimedOut("Service timed out")
      
      city = "TestCityTimeout"
      expected_report = f"Geocoding service timed out for {city}."
      expected_result = {"status": "error", "report": expected_report}

      result = get_current_time(city)

      self.assertEqual(result, expected_result)
      mock_geocode.assert_called_once_with(city, timeout=10)

  @patch('root_agent.agent.geolocator.geocode')
  def test_get_current_time_geocoding_unavailable_nominatim(self, mock_geocode):
      original_error = GeocoderUnavailable("Service unavailable")
      mock_geocode.side_effect = original_error
      
      city = "TestCityUnavailable"
      expected_report = f"Geocoding service unavailable/error for {city}: {original_error}"
      expected_result = {"status": "error", "report": expected_report}

      result = get_current_time(city)
      self.assertEqual(result, expected_result)
      mock_geocode.assert_called_once_with(city, timeout=10)

  @patch('root_agent.agent.tf') # Patch the 'tf' object directly
  @patch('root_agent.agent.geolocator.geocode')
  def test_get_current_time_timezone_not_found_tf(self, mock_geocode, mock_tf_object):
      mock_location = Mock()
      mock_location.latitude = 0.0 # e.g., Null Island
      mock_location.longitude = 0.0
      mock_geocode.return_value = mock_location

      mock_tf_object.timezone_at.return_value = None
      
      city = "NullIsland"
      expected_report = f"Could not determine timezone for {city} (lat: 0.0, lon: 0.0)."
      expected_result = {"status": "error", "report": expected_report}
      
      result = get_current_time(city)

      self.assertEqual(result, expected_result)
      mock_geocode.assert_called_once_with(city, timeout=10)
      mock_tf_object.timezone_at.assert_called_once_with(lng=0.0, lat=0.0)

  @patch('root_agent.agent.ZoneInfo', side_effect=ZoneInfoNotFoundError("Bogus timezone"))
  @patch('root_agent.agent.tf') # Patch the 'tf' object directly
  @patch('root_agent.agent.geolocator.geocode')
  def test_get_current_time_zoneinfo_error(self, mock_geocode, mock_tf_object, mock_zoneinfo_class):
      mock_location = Mock()
      mock_location.latitude = 43.6532
      mock_location.longitude = -79.3832
      mock_geocode.return_value = mock_location

      bogus_tz_string = "Bogus/Timezone"
      mock_tf_object.timezone_at.return_value = bogus_tz_string
      
      city = "Toronto"
      expected_report = f"Invalid timezone identifier '{bogus_tz_string}' found for {city}."
      expected_result = {"status": "error", "report": expected_report}

      result = get_current_time(city)

      self.assertEqual(result, expected_result)
      mock_geocode.assert_called_once_with(city, timeout=10)
      mock_tf_object.timezone_at.assert_called_once_with(lng=-79.3832, lat=43.6532)
      mock_zoneinfo_class.assert_called_once_with(bogus_tz_string)

if __name__ == '__main__':
  unittest.main()