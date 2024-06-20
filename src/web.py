html = """<!DOCTYPE html><html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<style>html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}
.buttonGreen { background-color: #4CAF50; border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }
.buttonRed { background-color: #D11D53; border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }
.center { text-align: center; margin-top: 20px;}
h1 {text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
</style></head>
<body><h1 class="center">Bentobox Wireless Controller</h1><br><br>
<form><button class="center" onclick="refreshPage()">refresh</button>
<br><br>
<button class="buttonGreen center" name="fan" value="turn_on" type="submit">Fan ON</button>
<br><br>
<button class="buttonRed center" name="fan" value="turn_off" type="submit">Fan OFF</button>
</form>
<br><br>
<br><br>
<p>%s<p>
    <script>
        function refreshPage() {
            window.location.href = 'http://' + window.location.hostname;
        }
    </script>
</body></html>
"""
