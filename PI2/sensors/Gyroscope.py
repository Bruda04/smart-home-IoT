from sensors import MPU6050
import time
import math


class Gyroscope:

    def __init__(self,
                 accel_threshold_g=0.3,
                 gyro_threshold_dps=50,
                 cooldown_time_s=2):
        try:
            self.mpu = MPU6050.MPU6050()
            self.mpu.dmp_initialize()
        except Exception as e:
            print(f"MPU6050 initialization error: {e}")

        self.accel_threshold = accel_threshold_g
        self.gyro_threshold = gyro_threshold_dps

        self.baseline = None

        self.last_trigger_time = 0
        self.cooldown = cooldown_time_s
    
    def get_data(self):
        try:
            accel = self.mpu.get_acceleration()
            gyro = self.mpu.get_rotation()

            accel_g = [
                accel[0] / 16384.0,
                accel[1] / 16384.0,
                accel[2] / 16384.0
            ]

            gyro_dps = [
                gyro[0] / 131.0,
                gyro[1] / 131.0,
                gyro[2] / 131.0
            ]

            return accel_g, gyro_dps

        except Exception:
            return None, None

    def is_significant_movement(self, accel_g, gyro_dps):
        if self.baseline is None:
            self.baseline = accel_g
            return False

        delta = math.sqrt(sum(
            (accel_g[i] - self.baseline[i]) ** 2 for i in range(3)
        ))

        gyro_magnitude = math.sqrt(sum(
            g ** 2 for g in gyro_dps
        ))

        current_time = time.time()

        if delta > self.accel_threshold or gyro_magnitude > self.gyro_threshold:
            if current_time - self.last_trigger_time > self.cooldown:
                self.last_trigger_time = current_time
                self.baseline = accel_g
                return True

        return False
