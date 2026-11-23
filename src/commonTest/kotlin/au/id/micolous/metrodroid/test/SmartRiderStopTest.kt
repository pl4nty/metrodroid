/*
 * SmartRiderStopTest.kt
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

import au.id.micolous.metrodroid.multi.FormattedString
import au.id.micolous.metrodroid.transit.Trip
import au.id.micolous.metrodroid.transit.smartrider.SmartRiderTagRecord
import au.id.micolous.metrodroid.transit.smartrider.SmartRiderType
import au.id.micolous.metrodroid.util.Preferences
import kotlin.test.Test
import kotlin.test.assertEquals

class SmartRiderStopTest : BaseInstrumentedTest() {
    private fun busTag(route: String, stopId: Int) = SmartRiderTagRecord(
        mTimestamp = 1L, isTapOn = true, mRoute = FormattedString(route), cost = 0,
        mode = Trip.Mode.BUS, isTransfer = false, mSmartRiderType = SmartRiderType.SMARTRIDER,
        mStopId = stopId
    )

    @Test
    fun testRailReplacementBusStop() {
        setLocale("en-AU")
        Preferences.showRawStationIds = false

        assertEquals("Maylands", busTag("902F", 0x7).station?.getStationName(false)?.unformatted)
    }

    @Test
    fun testOtherBusStopStaysUnknown() {
        setLocale("en-AU")
        Preferences.showRawStationIds = false

        // Bus stop IDs are only unique within a route.
        assertEquals("Unknown (0x7)", busTag("935", 0x7).station?.getStationName(false)?.unformatted)
    }
}
