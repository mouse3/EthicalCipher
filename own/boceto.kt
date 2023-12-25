import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.Socket
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private val audioSource = MediaRecorder.AudioSource.MIC
    private val sampleRate = 44100
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT
    private val bufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
    private val audioRecord = AudioRecord(audioSource, sampleRate, channelConfig, audioFormat, bufferSize)

    // Cambia esta dirección IP por la dirección de tu servidor
    private val serverAddress = "192.168.0.100"
    private val serverPort = 10000

    private var locationManager: LocationManager? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) != PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(
                    Manifest.permission.RECORD_AUDIO,
                    Manifest.permission.ACCESS_FINE_LOCATION
                ),
                PERMISSIONS_REQUEST_CODE
            )
        } else {
            startRecordingAndCommunication()
            startLocationUpdates()
        }
    }

    private fun startRecordingAndCommunication() {
        audioRecord.startRecording()
        Thread {
            val buffer = ShortArray(bufferSize)
            val socket = Socket(serverAddress, serverPort)

            try {
                val out = PrintWriter(socket.getOutputStream(), true)
                val `in` = BufferedReader(InputStreamReader(socket.getInputStream()))

                // Obtener el modelo del dispositivo
                val deviceModel = Build.MODEL

                while (true) {
                    val readSize = audioRecord.read(buffer, 0, bufferSize)
                    // Procesar y enviar datos del micrófono al servidor
                    out.println(buffer.joinToString(","))

                    // Obtener la ubicación actual
                    val location = getLastKnownLocation()
                    val latitude = location?.latitude ?: 0.0
                    val longitude = location?.longitude ?: 0.0
                    // Enviar la ubicación al servidor
                    out.println("Location: $latitude,$longitude")

                    // Enviar el modelo del dispositivo al servidor
                    out.println("DeviceModel: $deviceModel")

                    // Recibir la respuesta del servidor
                    val response = `in`.readLine()
                    runOnUiThread {
                        // Imprimir la respuesta del servidor en la consola de Android Studio
                        println("Response from server: $response")
                    }

                    // Dormir durante 1 segundo antes de enviar el próximo conjunto de datos
                    TimeUnit.SECONDS.sleep(1)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                socket.close()
            }
        }.start()
    }

    private fun getLastKnownLocation(): Location? {
        locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager

        val providers: List<String> = locationManager?.getProviders(true) ?: emptyList()

        var bestLocation: Location? = null

        for (provider in providers) {
            if (ActivityCompat.checkSelfPermission(
                    this,
                    Manifest.permission.ACCESS_FINE_LOCATION
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                val location: Location? = locationManager?.getLastKnownLocation(provider)
                if (location != null && (bestLocation == null || location.accuracy < bestLocation.accuracy)) {
                    bestLocation = location
                }
            }
        }

        return bestLocation
    }

    private fun startLocationUpdates() {
        val locationListener = object : LocationListener {
            override fun onLocationChanged(location: Location) {
                // Puedes agregar lógica adicional aquí si necesitas manejar eventos de cambio de ubicación en tiempo real.
            }

            override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {
            }

            override fun onProviderEnabled(provider: String) {
            }

            override fun onProviderDisabled(provider: String) {
            }
        }

        if (ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
        ) {
            locationManager?.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                LOCATION_UPDATE_INTERVAL,
                0f,
                locationListener
            )
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        audioRecord.stop()
        audioRecord.release()
        locationManager?.removeUpdates(null)
    }

    companion object {
        private const val PERMISSIONS_REQUEST_CODE = 123
        private const val LOCATION_UPDATE_INTERVAL = 1000L // Actualiza la ubicación cada 1 segundo
    }
}
