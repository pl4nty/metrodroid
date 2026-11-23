/*
 * SuicaTripTest.kt
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package au.id.micolous.metrodroid.test

import au.id.micolous.metrodroid.card.felica.FelicaBlock
import au.id.micolous.metrodroid.transit.Trip
import au.id.micolous.metrodroid.transit.suica.SuicaTrip
import au.id.micolous.metrodroid.util.ImmutableByteArray
import au.id.micolous.metrodroid.util.Preferences
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

/**
 * History records (service 0x090f) from a Welcome Suica used in Tokyo in November 2025.
 */
class SuicaTripTest : BaseInstrumentedTest() {
    private fun parse(hex: String, previousBalance: Int) =
        SuicaTrip.parse(FelicaBlock(ImmutableByteArray.fromHex(hex)), previousBalance)

    @Test
    fun testAirportBus() {
        setLocale("en-US")
        Preferences.showRawStationIds = false
        Preferences.showBothLocalAndEnglish = false

        // Haneda Airport bus: console 0x22, process 0x1d, operator 0xc69 (Keikyu Bus)
        val trip = parse("221D000033690C690000740E00000200", 5000)
        assertEquals(Trip.Mode.BUS, trip.mode)
        assertEquals(1300, trip.fareRaw)
        assertEquals(3700, trip.balance)
        val station = assertNotNull(trip.startStation)
        assertEquals("Keihin Express Bus", station.companyName?.unformatted)
        assertNull(trip.endStation)
    }

    @Test
    fun testTokyoBrt() {
        setLocale("en-US")
        Preferences.showRawStationIds = false
        Preferences.showBothLocalAndEnglish = false

        // Tokyo BRT: console 0x05 (bus), process 0x0f, operator 0xc8e
        val trip = parse("050F000F336A0C8E0000690900000B00", 2649)
        assertEquals(Trip.Mode.BUS, trip.mode)
        assertEquals(240, trip.fareRaw)
        val station = assertNotNull(trip.startStation)
        assertEquals("Tokyo BRT", station.companyName?.unformatted)

        setLocale("ja-JP")
        val tripJa = parse("050F000F336A0C8E0000690900000B00", 2649)
        assertEquals("東京BRT", tripJa.startStation?.companyName?.unformatted)
    }

    @Test
    fun testRailUnchanged() {
        setLocale("en-US")
        Preferences.showRawStationIds = false
        Preferences.showBothLocalAndEnglish = false

        // JR East Keiyō Line: Kaihin-Makuhari -> Tokyo
        val trip = parse("16010002336A3F120101390C00000400", 3700)
        assertEquals(Trip.Mode.METRO, trip.mode)
        assertEquals(571, trip.fareRaw)
        assertEquals("JR East", trip.startStation?.companyName?.unformatted)
        assertNotNull(trip.endStation)
    }
}
